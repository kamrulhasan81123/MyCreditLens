"""ML-layer tests for the application-PD model (§44).

Covers the dataset contract, artifact bundle, inference determinism, SHAP
execution, and the ApplicationToModelAdapter. Model-dependent tests skip
cleanly if the trained bundle or the raw dataset are absent.
"""

from datetime import date, datetime
from pathlib import Path

import pytest

from app.ai.application_adapter import ApplicationNotReadyError, ApplicationToModelAdapter
from app.ai.runtime import CreditModelRuntime, FeatureSchemaError
from app.config import settings
from ml.datasets.application_pd import (
    DATASET_FILENAME,
    EXCLUDED_COLUMNS,
    RAW_FEATURE_ORDER,
    TARGET_COLUMN,
    load_application_pd_frame,
)

pytestmark = pytest.mark.filterwarnings("ignore")

BUNDLE = settings.resolved_model_artifact_path
BUNDLE_AVAILABLE = (BUNDLE / "manifest.json").is_file()
requires_bundle = pytest.mark.skipif(not BUNDLE_AVAILABLE, reason="Active model bundle not present")

DATASET_PATH = Path(__file__).resolve().parents[2] / "dataset for training" / DATASET_FILENAME
DATASET_AVAILABLE = DATASET_PATH.is_file()
requires_dataset = pytest.mark.skipif(not DATASET_AVAILABLE, reason="Raw dataset not present")


# ---------------------------------------------------------------------------
# Dataset contract + leakage
# ---------------------------------------------------------------------------
@requires_dataset
def test_dataset_has_target_and_both_classes():
    frame, summary = load_application_pd_frame(DATASET_PATH)
    assert TARGET_COLUMN in frame.columns
    classes = set(frame[TARGET_COLUMN].unique().tolist())
    assert classes == {0, 1}
    assert summary.class_counts[0] > 0 and summary.class_counts[1] > 0


@requires_dataset
def test_dataset_is_deterministic():
    frame1, s1 = load_application_pd_frame(DATASET_PATH)
    frame2, s2 = load_application_pd_frame(DATASET_PATH)
    assert s1.sha256 == s2.sha256
    assert s1.clean_rows == s2.clean_rows
    assert list(frame1.columns) == list(frame2.columns)


@requires_dataset
def test_no_leakage_or_bureau_columns_in_features():
    frame, _ = load_application_pd_frame(DATASET_PATH)
    feature_cols = [c for c in frame.columns if c != TARGET_COLUMN]
    assert feature_cols == RAW_FEATURE_ORDER
    for banned in ("loan_grade", "loan_int_rate", "cred_hist_length", "historical_default", "Current_loan_status"):
        assert banned in EXCLUDED_COLUMNS
        assert banned not in feature_cols


# ---------------------------------------------------------------------------
# Artifact bundle + metadata
# ---------------------------------------------------------------------------
@requires_bundle
def test_bundle_loads_all_artifacts():
    runtime = CreditModelRuntime(BUNDLE)
    assert runtime.preprocessor is not None
    assert runtime.model is not None
    assert runtime.calibrator is not None
    assert runtime.explainer is not None
    assert runtime.schema["raw_feature_order"] == RAW_FEATURE_ORDER


@requires_bundle
def test_model_metadata_is_valid_and_version_is_human_readable():
    runtime = CreditModelRuntime(BUNDLE)
    md = runtime.metadata
    for key in (
        "model_name",
        "model_version",
        "algorithm",
        "dataset_sha256",
        "test_metrics",
        "calibration_method",
        "feature_schema_version",
        "limitations",
    ):
        assert key in md, f"metadata missing {key}"
    # Human-readable immutable version, not a UUID.
    assert md["model_version"] == "2.0.0"
    assert len(md["model_version"]) < 12 and md["model_version"].count("-") == 0
    assert 0.0 <= md["test_metrics"]["roc_auc"] <= 1.0


# ---------------------------------------------------------------------------
# Inference behaviour
# ---------------------------------------------------------------------------
def _fixture_features():
    return {
        "customer_age": 35.0,
        "customer_income": 60000.0,
        "employment_duration": 5.0,
        "home_ownership": "RENT",
        "loan_intent": "PERSONAL",
        "loan_amnt": 10000.0,
        "term_years": 4.0,
        "loan_percent_income": 10000.0 / 60000.0,
    }


@requires_bundle
def test_inference_probability_in_range_and_deterministic():
    runtime = CreditModelRuntime(BUNDLE)
    r1 = runtime.predict(_fixture_features())
    r2 = runtime.predict(_fixture_features())
    assert 0.0 <= r1.probability_of_default <= 1.0
    assert r1.probability_of_default == r2.probability_of_default  # deterministic
    assert r1.calibrated_probability == r1.probability_of_default
    assert 0.0 <= r1.raw_probability <= 1.0


@requires_bundle
def test_missing_feature_raises_schema_error():
    runtime = CreditModelRuntime(BUNDLE)
    incomplete = _fixture_features()
    del incomplete["customer_income"]
    with pytest.raises(FeatureSchemaError):
        runtime.predict(incomplete)


@requires_bundle
def test_extra_feature_is_ignored_and_order_preserved():
    runtime = CreditModelRuntime(BUNDLE)
    features = _fixture_features()
    features["unexpected_transaction_feature"] = 999.0  # must be ignored
    result = runtime.predict(features)
    assert 0.0 <= result.probability_of_default <= 1.0
    assert list(result.feature_values.keys()) == RAW_FEATURE_ORDER


@requires_bundle
def test_shap_execution_and_threshold_mapping():
    runtime = CreditModelRuntime(BUNDLE)
    result = runtime.predict(_fixture_features(), include_explanation=True)
    assert result.contributions  # non-empty SHAP contributions
    assert all("contribution" in c and "label" in c for c in result.contributions)
    # Threshold mapping is relative to the persisted (data-selected) thresholds.
    t = runtime.thresholds
    assert 0 < t.low_max < t.medium_max < 1
    assert t.band(t.low_max / 2) == "low"
    assert t.band((t.low_max + t.medium_max) / 2) == "medium"
    assert t.band((t.medium_max + 1) / 2) == "high"


# ---------------------------------------------------------------------------
# ApplicationToModelAdapter
# ---------------------------------------------------------------------------
def _schema():
    return {
        "raw_feature_order": RAW_FEATURE_ORDER,
        "numeric_features": [
            "customer_age",
            "customer_income",
            "employment_duration",
            "loan_amnt",
            "term_years",
            "loan_percent_income",
        ],
        "categorical_features": ["home_ownership", "loan_intent"],
        "feature_schema_version": "app_pd_2.0.0",
    }


class _Borrower:
    date_of_birth = date(1990, 1, 1)
    monthly_income_declared = 5000.0
    employment_duration_years = 6.0
    home_ownership = "RENT"


class _Application:
    submitted_at = datetime(2026, 1, 1)
    created_at = datetime(2026, 1, 1)
    loan_intent = "PERSONAL"
    requested_amount = 12000.0
    requested_term_months = 24


def test_adapter_builds_exact_feature_contract():
    adapter = ApplicationToModelAdapter(_schema())
    features = adapter.build_features(_Application(), _Borrower())
    assert list(features.keys()) == RAW_FEATURE_ORDER
    assert features["customer_income"] == 60000.0  # 5000 * 12
    assert features["term_years"] == 2.0  # 24 / 12
    assert abs(features["loan_percent_income"] - 12000.0 / 60000.0) < 1e-9
    assert features["home_ownership"] == "RENT"
    assert isinstance(features["customer_age"], float)


def test_adapter_missing_source_field_raises_not_ready():
    borrower = _Borrower()
    borrower.employment_duration_years = None
    adapter = ApplicationToModelAdapter(_schema())
    with pytest.raises(ApplicationNotReadyError):
        adapter.build_features(_Application(), borrower)


def test_adapter_invalid_category_raises_schema_error():
    borrower = _Borrower()
    borrower.home_ownership = "CASTLE"
    adapter = ApplicationToModelAdapter(_schema())
    with pytest.raises(FeatureSchemaError):
        adapter.build_features(_Application(), borrower)


def test_adapter_rejects_unmappable_schema_feature():
    schema = _schema()
    schema["raw_feature_order"] = RAW_FEATURE_ORDER + ["credit_score"]
    adapter = ApplicationToModelAdapter(schema)
    with pytest.raises(FeatureSchemaError):
        adapter.build_features(_Application(), _Borrower())


def test_adapter_dry_run_matches_schema():
    adapter = ApplicationToModelAdapter(_schema())
    dry = adapter.dry_run_features()
    assert list(dry.keys()) == RAW_FEATURE_ORDER


@requires_bundle
def test_model_discriminates_and_has_no_hard_zero_or_one():
    """A degenerate all-zero calibrator would pass every 0<=p<=1 assertion; this
    guards against it by requiring real separation and no hard 0/1 outputs."""
    runtime = CreditModelRuntime(BUNDLE)
    low = {
        "customer_age": 45.0,
        "customer_income": 120000.0,
        "employment_duration": 15.0,
        "home_ownership": "OWN",
        "loan_intent": "PERSONAL",
        "loan_amnt": 5000.0,
        "term_years": 2.0,
        "loan_percent_income": 5000.0 / 120000.0,
    }
    high = {
        "customer_age": 22.0,
        "customer_income": 14000.0,
        "employment_duration": 0.5,
        "home_ownership": "RENT",
        "loan_intent": "DEBTCONSOLIDATION",
        "loan_amnt": 12000.0,
        "term_years": 6.0,
        "loan_percent_income": 12000.0 / 14000.0,
    }
    pd_low = runtime.predict(low).probability_of_default
    pd_high = runtime.predict(high).probability_of_default
    assert pd_high > pd_low + 0.05, (pd_low, pd_high)  # materially different
    for p in (pd_low, pd_high):
        assert 0.0 < p < 1.0  # never exactly 0 or 1


@requires_bundle
def test_adapter_output_scores_through_runtime():
    """The adapter's output must be directly consumable by the runtime (proves
    the feature contract is aligned end-to-end)."""
    runtime = CreditModelRuntime(BUNDLE)
    adapter = ApplicationToModelAdapter(runtime.schema)
    features = adapter.build_features(_Application(), _Borrower())
    result = runtime.predict(features)
    assert 0.0 <= result.probability_of_default <= 1.0
