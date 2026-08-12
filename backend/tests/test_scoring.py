"""End-to-end tests for the application-PD scoring vertical slice (§19).

These tests exercise the REAL production scoring path — the same
ApplicationToModelAdapter, runtime, calibrator and SHAP explainer used by the
API. There is no separate fake scoring implementation.

They require the active trained bundle at settings.resolved_model_artifact_path
(backend/ml/artifacts/application_pd). If it is absent, model-dependent tests
are skipped with a clear reason rather than silently passing.
"""

import asyncio
import shutil

import pytest
from sqlalchemy import select

from app.config import settings
from app.models.borrower import Borrower
from app.schemas.auth import UserCreate
from app.services.auth_service import AuthService
from ml.contracts import write_manifest

pytestmark = pytest.mark.filterwarnings("ignore")

BUNDLE_AVAILABLE = (settings.resolved_model_artifact_path / "manifest.json").is_file()
requires_bundle = pytest.mark.skipif(
    not BUNDLE_AVAILABLE, reason="Active model bundle not present at MODEL_ARTIFACT_PATH"
)


# ---------------------------------------------------------------------------
# Helpers (mirror tests/test_workflow.py conventions)
# ---------------------------------------------------------------------------
def register_borrower(client, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "DemoPass123!", "full_name": "Test Borrower", "role": "borrower"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def create_staff(client, role: str, email: str) -> dict:
    async def create() -> None:
        async with client.session_factory() as session:
            await AuthService(session).register(
                UserCreate(email=email, password="DemoPass123!", full_name="Test Staff", role=role),
                allow_privileged=True,
            )

    asyncio.run(create())
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "DemoPass123!"})
    assert response.status_code == 200, response.text
    return response.json()


def set_borrower_fields(client, email: str, **fields) -> None:
    async def go() -> None:
        async with client.session_factory() as session:
            user = await AuthService(session)._get_user_by_email(email)
            borrower = (
                await session.execute(select(Borrower).where(Borrower.user_id == user.id))
            ).scalar_one()
            for key, value in fields.items():
                setattr(borrower, key, value)
            await session.commit()

    asyncio.run(go())


def grant_consent(client, tokens, application_id, data_source_type) -> None:
    response = client.post(
        f"/api/v1/applications/{application_id}/consents",
        headers=auth_header(tokens),
        json={"data_source_type": data_source_type},
    )
    assert response.status_code == 201, response.text


def make_scorable_application(client, email="borrower-score@example.com", *, grant_scoring_consent=True):
    """Build a fully scorable application through the public API + a direct DB
    write for fields not exposed on the borrower update schema (DOB)."""
    from datetime import date

    borrower = register_borrower(client, email)
    set_borrower_fields(
        client,
        email,
        borrower_type="individual",
        date_of_birth=date(1990, 1, 1),
        employment_type="full_time",
        monthly_income_declared=6000.0,
        employment_duration_years=5.0,
        home_ownership="RENT",
    )
    create = client.post(
        "/api/v1/applications/",
        headers=auth_header(borrower),
        json={
            "purpose": "Working capital",
            "loan_intent": "PERSONAL",
            "requested_amount": 8000,
            "requested_term_months": 24,
        },
    )
    assert create.status_code == 201, create.text
    application = create.json()
    grant_consent(client, borrower, application["id"], "bank_statement")
    if grant_scoring_consent:
        grant_consent(client, borrower, application["id"], "credit_scoring")
    submit = client.post(f"/api/v1/applications/{application['id']}/submit", headers=auth_header(borrower))
    assert submit.status_code == 200, submit.text
    return borrower, application["id"]


def score(client, staff, application_id):
    return client.post(f"/api/v1/applications/{application_id}/score", headers=auth_header(staff))


# ---------------------------------------------------------------------------
# 1-7, 12, 13, 19: successful scoring + persistence + response contract
# ---------------------------------------------------------------------------
@requires_bundle
def test_valid_application_scores_successfully_and_persists(client):
    _, application_id = make_scorable_application(client)
    analyst = create_staff(client, "credit_analyst", "analyst-score@example.com")

    response = score(client, analyst, application_id)
    assert response.status_code == 200, response.text
    body = response.json()

    # (1) success, (4) model name, (5) calibrated prob, (6) risk band
    assert 0.0 <= body["probability_of_default"] <= 1.0
    assert body["calibrated_probability"] is not None
    assert body["risk_band"] in {"low", "medium", "high"}
    assert body["model_name"] == "application_pd_hist_gradient_boosting"

    # (3, 19) real, human-readable model version — NOT a UUID
    assert body["model_version"] == "2.0.0"
    assert "-" not in body["model_version"]
    assert body["model_id"] != body["model_version"]
    assert body["feature_schema_version"] == "app_pd_2.0.0"

    # (12) OOD metadata, (13) uncertainty metadata
    assert "is_ood" in body and "ood_score" in body
    assert body["uncertainty"] is not None
    assert body["scoring_mode"] == "trained_artifact"
    assert body["explanation_available"] is True

    # (2) prediction persisted and retrievable with real version
    predictions = client.get(
        f"/api/v1/applications/{application_id}/predictions", headers=auth_header(analyst)
    )
    assert predictions.status_code == 200, predictions.text
    persisted = predictions.json()
    assert persisted["id"] == body["prediction_id"]
    assert persisted["model_version"] == "2.0.0"
    assert persisted["calibrated_probability"] is not None


@requires_bundle
def test_explanation_is_retrievable_after_scoring(client):
    _, application_id = make_scorable_application(client, email="borrower-expl@example.com")
    analyst = create_staff(client, "credit_analyst", "analyst-expl@example.com")
    assert score(client, analyst, application_id).status_code == 200

    explanation = client.get(
        f"/api/v1/applications/{application_id}/explanations", headers=auth_header(analyst)
    )
    assert explanation.status_code == 200, explanation.text
    body = explanation.json()
    assert body["method"] == "shap"
    assert body["shap_values"]  # non-empty
    # Explanation factors come from application features (transformed names),
    # not transaction features.
    keys = list(body["shap_values"].keys())
    assert any("customer_income" in k or "loan_percent_income" in k or "home_ownership" in k for k in keys)
    assert not any("dti_ratio" in k or "savings_rate" in k or "cashflow" in k for k in keys)


# ---------------------------------------------------------------------------
# 8: invalid feature value -> 422 ; missing data -> 409 ; consent -> 409
# ---------------------------------------------------------------------------
@requires_bundle
def test_invalid_feature_value_returns_422(client):
    borrower, application_id = make_scorable_application(client, email="borrower-422@example.com")
    # Present but invalid value (negative annualised income) -> the schema
    # cannot be satisfied by this value -> 422 (distinct from missing -> 409).
    set_borrower_fields(client, "borrower-422@example.com", monthly_income_declared=-500.0)
    analyst = create_staff(client, "credit_analyst", "analyst-422@example.com")
    response = score(client, analyst, application_id)
    assert response.status_code == 422, response.text


@requires_bundle
def test_missing_required_data_returns_409(client):
    borrower, application_id = make_scorable_application(client, email="borrower-409@example.com")
    # Null a required source field -> application not ready -> 409 (not 500).
    set_borrower_fields(client, "borrower-409@example.com", employment_duration_years=None)
    analyst = create_staff(client, "credit_analyst", "analyst-409@example.com")
    response = score(client, analyst, application_id)
    assert response.status_code == 409, response.text


@requires_bundle
def test_missing_scoring_consent_returns_409(client):
    borrower, application_id = make_scorable_application(
        client, email="borrower-noconsent@example.com", grant_scoring_consent=False
    )
    analyst = create_staff(client, "credit_analyst", "analyst-noconsent@example.com")
    response = score(client, analyst, application_id)
    assert response.status_code == 409, response.text
    assert "consent" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 9: missing model artifact -> 503
# ---------------------------------------------------------------------------
@requires_bundle
def test_missing_model_artifact_returns_503(client, tmp_path, monkeypatch):
    _, application_id = make_scorable_application(client, email="borrower-503@example.com")
    analyst = create_staff(client, "credit_analyst", "analyst-503@example.com")
    empty = tmp_path / "no_bundle"
    empty.mkdir()
    monkeypatch.setattr(settings, "model_artifact_path", str(empty))
    response = score(client, analyst, application_id)
    assert response.status_code == 503, response.text


# ---------------------------------------------------------------------------
# 10, 11: health endpoint truthfulness
# ---------------------------------------------------------------------------
@requires_bundle
def test_health_reports_ready_for_active_bundle(client):
    response = client.get("/health/model")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["model"]["model_version"] == "2.0.0"
    assert "dry_run_probability" in body["model"]


def test_health_not_ready_when_artifact_missing(client, tmp_path, monkeypatch):
    empty = tmp_path / "no_bundle"
    empty.mkdir()
    monkeypatch.setattr(settings, "model_artifact_path", str(empty))
    body = client.get("/health/model").json()
    assert body["status"] == "artifact_missing"
    assert body["status"] != "ready"


@requires_bundle
def test_health_detects_schema_incompatibility(client, tmp_path, monkeypatch):
    # Clone the active bundle and require a feature the adapter cannot produce.
    clone = tmp_path / "incompatible_bundle"
    shutil.copytree(settings.resolved_model_artifact_path, clone)
    schema_path = clone / "feature_schema.json"
    import json

    schema = json.loads(schema_path.read_text())
    schema["raw_feature_order"] = schema["raw_feature_order"] + ["credit_score"]
    schema_path.write_text(json.dumps(schema, indent=2, sort_keys=True))
    write_manifest(clone)  # re-checksum so the bundle still loads

    monkeypatch.setattr(settings, "model_artifact_path", str(clone))
    body = client.get("/health/model").json()
    assert body["status"] == "schema_incompatible", body
    assert body["status"] != "ready"


# ---------------------------------------------------------------------------
# 14, 15, 20: counterfactual + stress use the same path, no generic 500
# ---------------------------------------------------------------------------
@requires_bundle
def test_counterfactual_does_not_500_and_uses_same_baseline(client):
    _, application_id = make_scorable_application(client, email="borrower-cf@example.com")
    analyst = create_staff(client, "credit_analyst", "analyst-cf@example.com")
    scored = score(client, analyst, application_id).json()

    response = client.post(
        f"/api/v1/applications/{application_id}/counterfactuals",
        headers=auth_header(analyst),
        json={"target_probability": 0.1, "limit": 5},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    # (20) same feature builder path -> identical baseline probability.
    assert abs(body["original_probability"] - scored["probability_of_default"]) < 1e-9
    assert body["model_version"] == "2.0.0"


@requires_bundle
def test_counterfactual_returns_structured_error_not_500(client):
    borrower, application_id = make_scorable_application(client, email="borrower-cf409@example.com")
    set_borrower_fields(client, "borrower-cf409@example.com", monthly_income_declared=None)
    analyst = create_staff(client, "credit_analyst", "analyst-cf409@example.com")
    response = client.post(
        f"/api/v1/applications/{application_id}/counterfactuals",
        headers=auth_header(analyst),
        json={"target_probability": 0.1, "limit": 5},
    )
    assert response.status_code in {409, 422}, response.text
    assert response.status_code != 500


@requires_bundle
def test_stress_test_does_not_500(client):
    _, application_id = make_scorable_application(client, email="borrower-stress@example.com")
    analyst = create_staff(client, "credit_analyst", "analyst-stress@example.com")
    response = client.post(
        f"/api/v1/applications/{application_id}/stress-tests", headers=auth_header(analyst)
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["scenarios"]
    assert body["model_version"] == "2.0.0"


# ---------------------------------------------------------------------------
# 16, 17: staff data-source access vs cross-borrower isolation
# ---------------------------------------------------------------------------
def test_authorised_staff_can_access_application_data_sources(client):
    borrower, application_id = make_scorable_application(client, email="borrower-ds@example.com")
    analyst = create_staff(client, "credit_analyst", "analyst-ds@example.com")
    # Staff listing an application they may review must NOT 404.
    response = client.get(
        f"/api/v1/applications/{application_id}/data-sources", headers=auth_header(analyst)
    )
    assert response.status_code == 200, response.text


def test_authorised_staff_can_upload_data_source(client):
    borrower, application_id = make_scorable_application(client, email="borrower-ds2@example.com")
    analyst = create_staff(client, "credit_analyst", "analyst-ds2@example.com")
    csv = b"date,description,amount\n2025-01-01,Salary,5000\n2025-02-01,Salary,5000\n2025-03-01,Salary,5000\n"
    response = client.post(
        f"/api/v1/applications/{application_id}/data-sources?source_type=bank_statement",
        headers=auth_header(analyst),
        files={"file": ("stmt.csv", csv, "text/csv")},
    )
    # Previously this returned 404 for staff (owner-only check). Must succeed now.
    assert response.status_code == 200, response.text


def test_unrelated_borrower_cannot_access_data_sources(client):
    borrower, application_id = make_scorable_application(client, email="borrower-owner@example.com")
    intruder = register_borrower(client, "borrower-intruder@example.com")
    response = client.get(
        f"/api/v1/applications/{application_id}/data-sources", headers=auth_header(intruder)
    )
    assert response.status_code == 404, response.text


# ---------------------------------------------------------------------------
# 18: borrower creation role guard
# ---------------------------------------------------------------------------
def test_borrower_creation_role_guard(client):
    payload = {"borrower_type": "individual"}

    # Unauthenticated -> 401.
    assert client.post("/api/v1/borrowers/", json=payload).status_code == 401

    # Disallowed staff role -> 403.
    analyst = create_staff(client, "credit_analyst", "analyst-guard@example.com")
    denied = client.post("/api/v1/borrowers/", headers=auth_header(analyst), json=payload)
    assert denied.status_code == 403, denied.text

    # Allowed role (borrower) is not blocked by the guard (auto-created profile
    # means a repeat create is a 409 conflict, never a 403).
    borrower = register_borrower(client, "borrower-guard@example.com")
    allowed = client.post("/api/v1/borrowers/", headers=auth_header(borrower), json=payload)
    assert allowed.status_code in {201, 409}, allowed.text
    assert allowed.status_code != 403
