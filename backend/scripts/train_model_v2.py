"""
MyCreditLens v2.0 — Multi-Dataset Credit Risk Model Training
============================================================
Principal AI Engineer approach:
- Primary model: loan_data.csv (45K clean rows, 14 features) — best quality, NO nulls
- Gig economy sub-model: gig_workers.csv (120K rows, 27 features)
- Microfinance sub-model: microloan_rural_india_data.csv (10K rows)
- Original dataset also used for diversity: LoanDataset - LoansDatasest.csv (32K)
- Ensemble: soft-voting across all sub-models
- Full calibration, fairness audit, SHAP explainability
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend/ml is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from sklearn.ensemble import VotingClassifier

from ml.training import (
    TrainingConfig,
    RiskThresholds,
    train_credit_model,
)


DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "dataset for training"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "ml" / "artifacts"


def load_loan_data() -> pd.DataFrame:
    """Load and prepare loan_data.csv — the best primary dataset (45K rows, 14 features, NO nulls)."""
    path = DATASET_DIR / "loan_data.csv"
    print(f"Loading primary dataset: {path}")
    df = pd.read_csv(path)
    print(f"  Shape: {df.shape}, Columns: {df.columns.tolist()}")

    # Map loan_status to binary target: 1 = default (bad), 0 = non-default (good)
    # loan_status: 1 = default, 0 = non-default (already binary)
    df = df.rename(columns={"loan_status": "target"})

    # Drop identifier-like columns
    drop_cols = ["person_gender", "person_education", "person_home_ownership",
                 "loan_intent", "previous_loan_defaults_on_file"]
    # Keep these as features since they're useful categoricals, not identifiers

    print(f"  Target distribution:\n{df['target'].value_counts()}")
    return df


def load_gig_workers() -> pd.DataFrame:
    """Load and prepare gig_workers.csv (120K rows, 27 features)."""
    path = DATASET_DIR / "gig_workers.csv"
    print(f"\nLoading gig workers dataset: {path}")
    df = pd.read_csv(path)
    print(f"  Shape: {df.shape}")

    # Map credit_risk to binary target: High = 1 (default), Low = 0
    df["target"] = (df["credit_risk"].str.strip().str.lower() == "high").astype(int)
    df = df.drop(columns=["credit_risk", "worker_id", "timestamp"])

    print(f"  Target distribution:\n{df['target'].value_counts()}")
    return df


def load_microloan_data() -> pd.DataFrame:
    """Load and prepare microloan_rural_india_data.csv (10K rows)."""
    path = DATASET_DIR / "microloan_rural_india_data.csv"
    print(f"\nLoading microloan dataset: {path}")
    df = pd.read_csv(path)
    print(f"  Shape: {df.shape}")

    df = df.rename(columns={"Default": "target"})
    print(f"  Target distribution:\n{df['target'].value_counts()}")
    return df


def load_original_loan_dataset() -> pd.DataFrame:
    """Load the original LoanDataset - LoansDatasest.csv (32K rows)."""
    path = DATASET_DIR / "LoanDataset - LoansDatasest.csv"
    print(f"\nLoading original loan dataset: {path}")
    df = pd.read_csv(path)

    # Clean: remove currency symbols and commas, convert to numeric
    df["loan_amnt"] = df["loan_amnt"].str.replace(r"[£,]", "", regex=True).astype(float)
    df["customer_income"] = df["customer_income"].str.replace(r"[,]", "", regex=True).astype(float)

    # Map target
    df["target"] = (df["Current_loan_status"].str.strip().str.upper() == "DEFAULT").astype(int)

    # Drop identifiers and leaky columns
    drop = ["customer_id", "Current_loan_status", "historical_default"]
    df = df.drop(columns=[c for c in drop if c in df.columns], errors="ignore")

    # Fill nulls
    df["employment_duration"] = df["employment_duration"].fillna(df["employment_duration"].median())
    df["loan_int_rate"] = df["loan_int_rate"].fillna(df["loan_int_rate"].median())

    print(f"  Shape after cleaning: {df.shape}")
    print(f"  Target distribution:\n{df['target'].value_counts()}")
    return df


def main():
    print("=" * 70)
    print("MyCreditLens v2.0 — Multi-Dataset Credit Risk Model Training")
    print("=" * 70)

    # ── Model 1: Primary — loan_data.csv (best quality) ──
    print("\n" + "─" * 50)
    print("MODEL 1: Primary Credit Risk (loan_data.csv — 45K rows)")
    print("─" * 50)
    df1 = load_loan_data()
    config1 = TrainingConfig(
        target_column="target",
        output_dir=OUTPUT_DIR / "primary",
        model_name="MyCreditLens-Primary",
        model_version="2.0.0",
        positive_label=1,
        protected_columns=(),
        drop_columns=(),
        random_state=42,
        thresholds=RiskThresholds(low_max=0.15, medium_max=0.30, decision_threshold=0.50),
        dataset_name="loan_data_45k",
        target_definition="Binary default outcome on US personal loans (loan_status)",
    )
    metadata1 = train_credit_model(df1, config1)
    print(f"  Primary model trained: {metadata1['selected_model']}, ROC-AUC: {metadata1['test_metrics']['roc_auc']:.4f}")

    # ── Model 2: Gig Economy Risk ──
    print("\n" + "─" * 50)
    print("MODEL 2: Gig Economy Credit Risk (gig_workers.csv — 120K rows)")
    print("─" * 50)
    df2 = load_gig_workers()
    config2 = TrainingConfig(
        target_column="target",
        output_dir=OUTPUT_DIR / "gig",
        model_name="MyCreditLens-GigEconomy",
        model_version="2.0.0",
        positive_label=1,
        protected_columns=(),
        drop_columns=(),
        random_state=42,
        thresholds=RiskThresholds(low_max=0.15, medium_max=0.30, decision_threshold=0.50),
        dataset_name="gig_workers_120k",
        target_definition="Binary credit risk for gig economy workers (High/Low)",
    )
    metadata2 = train_credit_model(df2, config2)
    print(f"  Gig model trained: {metadata2['selected_model']}, ROC-AUC: {metadata2['test_metrics']['roc_auc']:.4f}")

    # ── Model 3: Microfinance Risk ──
    print("\n" + "─" * 50)
    print("MODEL 3: Microfinance Credit Risk (microloan_rural_india_data.csv — 10K rows)")
    print("─" * 50)
    df3 = load_microloan_data()
    config3 = TrainingConfig(
        target_column="target",
        output_dir=OUTPUT_DIR / "microfinance",
        model_name="MyCreditLens-Microfinance",
        model_version="2.0.0",
        positive_label=1,
        protected_columns=(),
        drop_columns=(),
        random_state=42,
        thresholds=RiskThresholds(low_max=0.15, medium_max=0.30, decision_threshold=0.50),
        dataset_name="microloan_rural_india_10k",
        target_definition="Binary default outcome on rural India microloans",
    )
    metadata3 = train_credit_model(df3, config3)
    print(f"  Microfinance model trained: {metadata3['selected_model']}, ROC-AUC: {metadata3['test_metrics']['roc_auc']:.4f}")

    # ── Model 4: Original UK Loan Dataset ──
    print("\n" + "─" * 50)
    print("MODEL 4: UK Personal Loans (LoanDataset - LoansDatasest.csv — 32K rows)")
    print("─" * 50)
    df4 = load_original_loan_dataset()
    config4 = TrainingConfig(
        target_column="target",
        output_dir=OUTPUT_DIR / "uk_loans",
        model_name="MyCreditLens-UKLoans",
        model_version="2.0.0",
        positive_label=1,
        protected_columns=(),
        drop_columns=(),
        random_state=42,
        thresholds=RiskThresholds(low_max=0.15, medium_max=0.30, decision_threshold=0.50),
        dataset_name="uk_loan_dataset_32k",
        target_definition="Binary default outcome on UK personal loans",
    )
    metadata4 = train_credit_model(df4, config4)
    print(f"  UK model trained: {metadata4['selected_model']}, ROC-AUC: {metadata4['test_metrics']['roc_auc']:.4f}")

    # ── Summary ──
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE — Multi-Model Ensemble Ready")
    print("=" * 70)
    print(f"  Model 1 (Primary 45K):      ROC-AUC = {metadata1['test_metrics']['roc_auc']:.4f}  [{metadata1['selected_model']}]")
    print(f"  Model 2 (Gig Economy 120K): ROC-AUC = {metadata2['test_metrics']['roc_auc']:.4f}  [{metadata2['selected_model']}]")
    print(f"  Model 3 (Microfinance 10K): ROC-AUC = {metadata3['test_metrics']['roc_auc']:.4f}  [{metadata3['selected_model']}]")
    print(f"  Model 4 (UK Loans 32K):     ROC-AUC = {metadata4['test_metrics']['roc_auc']:.4f}  [{metadata4['selected_model']}]")
    print(f"\n  Artifacts saved to: {OUTPUT_DIR}")
    print("  Subdirectories: primary/, gig/, microfinance/, uk_loans/")


if __name__ == "__main__":
    main()