"""Canonical feature contract and dataset loader for the application-level
probability-of-default (PD) model.

This is the single source of truth for *which* features the application PD
model consumes. Both the training pipeline (`ml.train_application_pd`) and the
inference-time adapter (`app.ai.application_adapter.ApplicationToModelAdapter`)
agree on this contract:

  * The trainer writes these feature names into ``feature_schema.json``.
  * The adapter reads ``feature_schema.json`` at runtime and produces exactly
    these names/types from persisted Application + Borrower data.

Every feature here is *inference-safe*: it can be reproduced deterministically
from a real MyCreditLens application at scoring time. Bureau- or lender-assigned
columns present in the raw dataset (``loan_grade``, ``loan_int_rate``,
``cred_hist_length``, ``historical_default``) are deliberately EXCLUDED because
MyCreditLens has no source for them and fabricating them would be invalid.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Feature contract (single source of truth)
# ---------------------------------------------------------------------------

FEATURE_SCHEMA_VERSION = "app_pd_2.0.0"

TARGET_COLUMN = "target"

NUMERIC_FEATURES = [
    "customer_age",
    "customer_income",
    "employment_duration",
    "loan_amnt",
    "term_years",
    "loan_percent_income",
]

CATEGORICAL_FEATURES = [
    "home_ownership",
    "loan_intent",
]

# Order the model sees raw features in (preserved through the preprocessor).
RAW_FEATURE_ORDER = [
    "customer_age",
    "customer_income",
    "employment_duration",
    "home_ownership",
    "loan_intent",
    "loan_amnt",
    "term_years",
    "loan_percent_income",
]

# Allowed category levels (match the raw dataset exactly; the adapter validates
# against these and raises rather than inventing an unseen level).
HOME_OWNERSHIP_LEVELS = ["RENT", "OWN", "MORTGAGE", "OTHER"]
LOAN_INTENT_LEVELS = [
    "PERSONAL",
    "EDUCATION",
    "MEDICAL",
    "VENTURE",
    "HOMEIMPROVEMENT",
    "DEBTCONSOLIDATION",
]

# Plausibility bounds used ONLY for deterministic cleaning of dirty raw training
# values (the raw file contains e.g. age=3 and age=144). Real applications never
# hit these because age is derived from a validated date of birth.
AGE_MIN, AGE_MAX = 18, 100
EMPLOYMENT_DURATION_MIN, EMPLOYMENT_DURATION_MAX = 0.0, 50.0
LOAN_PERCENT_INCOME_MAX = 10.0

DATASET_FILENAME = "LoanDataset - LoansDatasest.csv"
DATASET_NAME = "loan_dataset_uk_32k"
TARGET_DEFINITION = (
    "Binary personal-loan default outcome derived from Current_loan_status: "
    "1 = DEFAULT, 0 = NO DEFAULT. Provenance of the underlying public CSV is "
    "undocumented in the repository; treat metrics as development-grade, not "
    "evidence of real-world or Malaysian-market performance."
)

# Columns intentionally excluded from the inference-safe model, with reasons.
EXCLUDED_COLUMNS = {
    "loan_grade": "Bureau/lender-assigned risk grade; not collected by MyCreditLens.",
    "loan_int_rate": "Lender-set rate derived from loan_grade; circular and not available at decision time.",
    "cred_hist_length": "Requires a credit bureau MyCreditLens does not integrate.",
    "historical_default": "Prior-default bureau flag; ~63% missing and not collected.",
    "customer_id": "Row identifier; not predictive.",
    "Current_loan_status": "Raw target column (mapped into `target`).",
}


@dataclass(frozen=True)
class DatasetSummary:
    path: str
    sha256: str
    raw_rows: int
    clean_rows: int
    duplicates_dropped: int
    null_target_dropped: int
    class_counts: dict
    missing_profile: dict


def _to_float_series(series: pd.Series) -> pd.Series:
    """Parse currency/number-like strings ('£35,000.00', '59000') to float."""
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    cleaned = (
        series.astype(str)
        .str.replace(r"[^0-9.\-]", "", regex=True)
        .replace({"": np.nan, "-": np.nan, ".": np.nan})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def load_application_pd_frame(csv_path: str | Path) -> tuple[pd.DataFrame, DatasetSummary]:
    """Load and deterministically clean the LoanDataset into the inference-safe
    feature frame (8 features + ``target``). Cleaning is fully deterministic so
    the dataset hash + row counts are reproducible.
    """
    csv_path = Path(csv_path)
    raw = pd.read_csv(csv_path)
    raw_rows = len(raw)

    df = raw.copy()

    # --- target ---------------------------------------------------------
    status = df["Current_loan_status"].astype(str).str.strip().str.upper()
    df["target"] = np.where(status == "DEFAULT", 1, np.where(status == "NO DEFAULT", 0, np.nan))
    null_target = int(df["target"].isna().sum())
    df = df[df["target"].notna()].copy()
    df["target"] = df["target"].astype(int)

    # --- numeric parsing ------------------------------------------------
    df["customer_income"] = _to_float_series(df["customer_income"])
    df["loan_amnt"] = _to_float_series(df["loan_amnt"])
    df["customer_age"] = _to_float_series(df["customer_age"])
    df["employment_duration"] = _to_float_series(df["employment_duration"])
    df["term_years"] = _to_float_series(df["term_years"])

    # --- deterministic cleaning of erroneous raw values -----------------
    df["customer_age"] = df["customer_age"].clip(lower=AGE_MIN, upper=AGE_MAX)
    df["employment_duration"] = df["employment_duration"].clip(
        lower=EMPLOYMENT_DURATION_MIN, upper=EMPLOYMENT_DURATION_MAX
    )

    # --- derived feature: loan as a fraction of annual income -----------
    income = df["customer_income"].replace({0: np.nan})
    df["loan_percent_income"] = (df["loan_amnt"] / income).clip(lower=0.0, upper=LOAN_PERCENT_INCOME_MAX)

    # --- categoricals ---------------------------------------------------
    df["home_ownership"] = df["home_ownership"].astype(str).str.strip().str.upper()
    df["loan_intent"] = df["loan_intent"].astype(str).str.strip().str.upper()

    features = df[RAW_FEATURE_ORDER + ["target"]].copy()

    before = len(features)
    features = features.drop_duplicates().reset_index(drop=True)
    duplicates_dropped = before - len(features)

    missing_profile = {col: float(features[col].isna().mean()) for col in RAW_FEATURE_ORDER}

    summary = DatasetSummary(
        path=str(csv_path),
        sha256=_sha256(csv_path),
        raw_rows=raw_rows,
        clean_rows=len(features),
        duplicates_dropped=duplicates_dropped,
        null_target_dropped=null_target,
        class_counts=features["target"].value_counts().sort_index().to_dict(),
        missing_profile=missing_profile,
    )
    return features, summary


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
