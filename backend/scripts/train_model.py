"""Train the MyCreditLens credit risk model on the provided loan dataset.

Run from the backend directory: python scripts/train_model.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Ensure backend is on the path before importing project modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.contracts import RiskThresholds  # noqa: E402
from ml.training import TrainingConfig, train_credit_model  # noqa: E402


def load_and_preprocess(csv_path: str) -> pd.DataFrame:
    """Load and clean the loan dataset for training."""
    df = pd.read_csv(csv_path)

    # Drop rows with missing target
    df = df.dropna(subset=["Current_loan_status"])

    # Map target: DEFAULT -> 1, NO DEFAULT -> 0
    df["target"] = (df["Current_loan_status"].str.strip().str.upper() == "DEFAULT").astype(int)

    # Clean loan_amnt: remove currency symbols and commas
    df["loan_amnt"] = (
        df["loan_amnt"]
        .astype("string")
        .str.replace(r"[£$,]", "", regex=True)
        .astype(float)
    )

    # Clean customer_income: remove commas, convert to float
    df["customer_income"] = (
        df["customer_income"]
        .astype("string")
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    # Drop identifier columns and columns with too many nulls
    drop_cols = ["customer_id", "Current_loan_status", "historical_default"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    # Drop rows where loan_int_rate is null (3116 nulls is too many to impute well)
    df = df.dropna(subset=["loan_int_rate"])

    # Fill remaining nulls
    df["employment_duration"] = df["employment_duration"].fillna(df["employment_duration"].median())

    print(f"Cleaned dataset: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Target distribution:\n{df['target'].value_counts()}")
    print(f"Features: {[c for c in df.columns if c != 'target']}")

    return df


def main():
    dataset_path = Path(__file__).resolve().parent.parent.parent / "dataset for training" / "LoanDataset - LoansDatasest.csv"
    output_dir = Path(__file__).resolve().parent.parent / "ml" / "artifacts"

    print(f"Loading dataset from: {dataset_path}")
    df = load_and_preprocess(str(dataset_path))

    config = TrainingConfig(
        target_column="target",
        output_dir=output_dir,
        model_name="MyCreditLensCreditRisk",
        model_version="1.0.0",
        positive_label=1,
        protected_columns=(),
        drop_columns=(),
        random_state=42,
        thresholds=RiskThresholds(low_max=0.15, medium_max=0.30, decision_threshold=0.50),
        dataset_name="loan_credit_risk_32k",
        target_definition="Binary default outcome: DEFAULT vs NO DEFAULT on personal loans",
    )

    print(f"\nTraining model... Output dir: {output_dir}")
    metadata = train_credit_model(df, config)

    print(f"\n=== Training Complete ===")
    print(f"Model: {metadata['model_name']} v{metadata['model_version']}")
    print(f"Selected estimator: {metadata['selected_model']}")
    print(f"Calibration: {metadata['calibration_method']}")
    print(f"Rows: {metadata['row_counts']}")
    print(f"\nTest Metrics:")
    for k, v in metadata["test_metrics"].items():
        if isinstance(v, (int, float)):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")
    print(f"\nArtifacts saved to: {output_dir}")


if __name__ == "__main__":
    main()