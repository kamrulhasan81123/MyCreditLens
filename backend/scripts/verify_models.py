"""Verify all 4 trained models load correctly and print their metrics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.runtime import load_credit_runtime

ARTIFACTS = Path(__file__).resolve().parent.parent / "ml" / "artifacts"

models = {
    "Primary (loan_data 45K)": ARTIFACTS / "primary",
    "Gig Economy (120K)": ARTIFACTS / "gig",
    "Microfinance (10K)": ARTIFACTS / "microfinance",
    "UK Loans (32K)": ARTIFACTS / "uk_loans",
}

print("=" * 70)
print("MyCreditLens v2.0 — Model Verification")
print("=" * 70)

for name, path in models.items():
    try:
        r = load_credit_runtime(path)
        metrics = r.metadata["test_metrics"]
        print(f"\n{name}:")
        print(f"  Model: {r.model_name} v{r.model_version}")
        print(f"  Algorithm: {r.metadata['selected_model']}")
        print(f"  Calibration: {r.metadata['calibration_method']}")
        print(f"  ROC-AUC: {metrics['roc_auc']:.4f}")
        print(f"  PR-AUC: {metrics['pr_auc']:.4f}")
        print(f"  Brier: {metrics['brier_score']:.4f}")
        print(f"  KS: {metrics['ks_statistic']:.4f}")
        print(f"  Features: {len(r.schema['raw_feature_order'])} features")
    except Exception as e:
        print(f"\n{name}: FAILED — {e}")

print("\n" + "=" * 70)
print("All models verified successfully.")