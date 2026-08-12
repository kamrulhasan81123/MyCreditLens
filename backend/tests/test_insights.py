"""Tests for model-metadata, monitoring, fairness, and calibration endpoints."""

import asyncio

import pytest

from app.config import BACKEND_DIR, settings
from app.schemas.auth import UserCreate
from app.services.auth_service import AuthService

pytestmark = pytest.mark.filterwarnings("ignore")

BUNDLE = (settings.resolved_model_artifact_path / "manifest.json").is_file()
requires_bundle = pytest.mark.skipif(not BUNDLE, reason="Active bundle not present")
DATASET = (BACKEND_DIR.parent / "dataset for training" / "LoanDataset - LoansDatasest.csv").is_file()
requires_dataset = pytest.mark.skipif(not DATASET, reason="Eval dataset not present")


def register(client, email, role="borrower"):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "DemoPass123!", "full_name": "Test User", "role": role})
    assert r.status_code == 201, r.text
    return r.json()


def staff(client, role, email):
    async def go():
        async with client.session_factory() as s:
            await AuthService(s).register(UserCreate(email=email, password="DemoPass123!", full_name="Staff User", role=role), allow_privileged=True)
    asyncio.run(go())
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "DemoPass123!"})
    assert r.status_code == 200
    return r.json()


def hdr(t):
    return {"Authorization": f"Bearer {t['access_token']}"}


@requires_bundle
def test_model_metadata_is_safe_and_versioned(client):
    b = register(client, "meta-b@example.com")
    r = client.get("/api/v1/models/metadata", headers=hdr(b))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["model_version"] == "2.0.0"
    assert body["algorithm"] == "hist_gradient_boosting"
    assert "development-grade" in body["dataset_provenance_status"].lower()
    # No filesystem paths / secrets leaked.
    blob = str(body).lower()
    assert "c:\\" not in blob and "/users/" not in blob and "model_path" not in body
    assert "jwt" not in blob and "secret" not in blob


@requires_bundle
def test_active_model_and_registry_sync(client):
    admin = staff(client, "admin", "meta-admin@example.com")
    synced = client.post("/api/v1/models/registry/sync", headers=hdr(admin))
    assert synced.status_code == 200, synced.text
    assert synced.json()["version"] == "2.0.0" and synced.json()["is_active"] is True
    active = client.get("/api/v1/models/active", headers=hdr(admin))
    assert active.status_code == 200
    assert active.json()["registered"] is True


@requires_bundle
def test_monitoring_summary_does_not_fabricate_performance(client):
    analyst = staff(client, "credit_analyst", "mon-analyst@example.com")
    r = client.get("/api/v1/monitoring/summary", headers=hdr(analyst))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["performance_status"] == "outcome_data_unavailable"
    assert body["active_model_version"] == "2.0.0"
    assert "pd_distribution" in body and "risk_band_distribution" in body
    # No fabricated production discrimination metric.
    assert "roc_auc" not in body


def test_monitoring_forbidden_for_borrower(client):
    b = register(client, "mon-borrower@example.com")
    r = client.get("/api/v1/monitoring/summary", headers=hdr(b))
    assert r.status_code == 403


@requires_bundle
@requires_dataset
def test_age_band_fairness_audit(client):
    reviewer = staff(client, "compliance_reviewer", "fair-rev@example.com")
    r = client.get("/api/v1/fairness/age-band-audit", headers=hdr(reviewer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "evaluated"
    assert "certification" not in body["note"].lower() or "not a legal" in body["note"].lower()
    assert set(body["groups"].keys()) >= {"18-24", "25-34", "35-44"}
    # Small groups flagged.
    for g in body["groups"].values():
        if g.get("sample_count", 0) and g["sample_count"] < 50:
            assert g["small_group_warning"] is True
    assert body["disparate_impact_ratio"] is not None


def test_fairness_forbidden_for_analyst_role_scope(client):
    # Fairness is admin/compliance only; a plain borrower is forbidden.
    b = register(client, "fair-borrower@example.com")
    r = client.get("/api/v1/fairness/age-band-audit", headers=hdr(b))
    assert r.status_code == 403


@requires_bundle
@requires_dataset
def test_calibration_by_segment_handles_small_samples(client):
    reviewer = staff(client, "compliance_reviewer", "cal-rev@example.com")
    r = client.get("/api/v1/calibration/segments", headers=hdr(reviewer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "evaluated"
    # Any segment below threshold must be marked insufficient, not fabricated.
    for seg in body["segments"].values():
        if seg.get("status") == "insufficient_sample":
            assert "brier_score" not in seg
