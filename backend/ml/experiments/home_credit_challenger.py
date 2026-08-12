"""RESEARCH challenger experiment — Home Credit Default Risk (application-only).

This trains a challenger PD model on the Home Credit `train.csv` using ONLY the
features that MyCreditLens can reproduce at inference time (the inference-safe
intersection with the active model's contract). It deliberately EXCLUDES
`external_source_1/2/3` (proprietary bureau credit scores, not available to
MyCreditLens) and every secondary table (bureau / previous / installments / …).

It is a RESEARCH artifact only. It is written to `ml/artifacts/_challenger/…`,
never to the active `MODEL_ARTIFACT_PATH`, and does not touch model 2.0.0.

Two questions it answers with executed code:
  1. What held-out discrimination/calibration does an application-only Home Credit
     model achieve (without the proprietary EXT_SOURCE features)?
  2. Do real MyCreditLens-scale inputs fall inside or outside this model's
     training support? (Home Credit loan/income magnitudes are ~25-60x larger.)

Run (from backend/):
    .venv\\Scripts\\python -m ml.experiments.home_credit_challenger
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.evaluation import classification_metrics

RANDOM_STATE = 42
DATASET = Path("../dataset for training/archive (5)/train.csv")
OUT = Path("ml/artifacts/_challenger/home_credit_2_1_0")

# Inference-safe intersection with the active MyCreditLens contract.
NUMERIC = ["customer_age", "customer_income", "employment_duration", "loan_amnt", "loan_percent_income"]
CATEGORICAL = ["home_ownership"]
FEATURES = NUMERIC + CATEGORICAL

# Home Credit housing_type_name -> MyCreditLens home_ownership levels.
HOUSING_MAP = {
    "House / apartment": "OWN",
    "Office apartment": "OWN",
    "Co-op apartment": "OWN",
    "Rented apartment": "RENT",
    "Municipal apartment": "RENT",
    "With parents": "OTHER",
}

EXCLUDED = {
    "external_source_1/2/3": "Proprietary external credit scores; not available to MyCreditLens at inference (bureau-derived).",
    "loan_intent": "Home Credit has contract type (Cash/Revolving), not loan purpose; cannot reproduce MyCreditLens loan_intent.",
    "term_years": "Only approximable from loan_body/annuity; excluded to keep the contract clean.",
    "all secondary tables": "bureau/previous/installments/POS/credit_card excluded (application-only, point-in-time).",
}


def build_frame() -> pd.DataFrame:
    cols = ["target", "income", "loan_body", "days_birth", "days_employed", "housing_type_name"]
    df = pd.read_csv(DATASET, usecols=cols)
    out = pd.DataFrame()
    out["customer_age"] = (-df["days_birth"] / 365.25).clip(18, 100)
    emp = -df["days_employed"] / 365.25
    emp[df["days_employed"] >= 365243] = np.nan  # pensioner sentinel
    out["employment_duration"] = emp.clip(0, 50)
    out["customer_income"] = df["income"].astype(float)
    out["loan_amnt"] = df["loan_body"].astype(float)
    out["loan_percent_income"] = (out["loan_amnt"] / out["customer_income"].replace({0: np.nan})).clip(0, 10)
    out["home_ownership"] = df["housing_type_name"].map(HOUSING_MAP).fillna("OTHER")
    out["target"] = df["target"].astype(int)
    return out.dropna(subset=["customer_income", "loan_amnt"]).reset_index(drop=True)


def build_preprocessor() -> ColumnTransformer:
    num = Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())])
    cat = Pipeline([("imp", SimpleImputer(strategy="most_frequent")), ("enc", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    return ColumnTransformer([("numeric", num, NUMERIC), ("categorical", cat, CATEGORICAL)], remainder="drop", verbose_feature_names_out=True)


def main() -> None:
    frame = build_frame()
    y = frame["target"].to_numpy()
    X = frame[FEATURES]
    tr, ho, ytr, yho = train_test_split(X, y, train_size=0.70, stratify=y, random_state=RANDOM_STATE)
    val, te, yval, yte = train_test_split(ho, yho, train_size=0.50, stratify=yho, random_state=RANDOM_STATE + 1)

    pre = build_preprocessor()
    Xtr = np.asarray(pre.fit_transform(tr), dtype=float)
    Xval = np.asarray(pre.transform(val), dtype=float)
    Xte = np.asarray(pre.transform(te), dtype=float)

    pos_weight = float((ytr == 0).sum() / max((ytr == 1).sum(), 1))
    candidates = {
        "logistic_regression": LogisticRegression(class_weight="balanced", max_iter=2000, random_state=RANDOM_STATE),
        "hist_gradient_boosting": HistGradientBoostingClassifier(learning_rate=0.05, max_iter=300, max_leaf_nodes=31, l2_regularization=1.0, random_state=RANDOM_STATE),
    }
    try:
        import xgboost as xgb

        candidates["xgboost"] = xgb.XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, scale_pos_weight=pos_weight, tree_method="hist", eval_metric="logloss", random_state=RANDOM_STATE, n_jobs=-1)
    except Exception:
        pass
    try:
        import lightgbm as lgb

        candidates["lightgbm"] = lgb.LGBMClassifier(n_estimators=300, num_leaves=31, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1, verbose=-1)
    except Exception:
        pass

    from sklearn.metrics import roc_auc_score

    val_metrics = {}
    fitted = {}
    for name, est in candidates.items():
        est.fit(Xtr, ytr)
        fitted[name] = est
        val_metrics[name] = classification_metrics(yval, est.predict_proba(Xval)[:, 1], 0.5)
    selected = max(val_metrics, key=lambda n: (val_metrics[n]["roc_auc"], val_metrics[n]["pr_auc"]))

    # Honest calibration (fit on one val half, select on the other).
    Xcf, Xcs, ycf, ycs = train_test_split(Xval, yval, train_size=0.5, stratify=yval, random_state=RANDOM_STATE + 2)
    cal_metrics = {}
    for method in ("sigmoid", "isotonic"):
        try:
            from sklearn.frozen import FrozenEstimator

            c = CalibratedClassifierCV(FrozenEstimator(fitted[selected]), method=method)
        except ImportError:
            c = CalibratedClassifierCV(fitted[selected], method=method, cv="prefit")
        c.fit(Xcf, ycf)
        cal_metrics[method] = classification_metrics(ycs, np.clip(c.predict_proba(Xcs)[:, 1], 1e-4, 1 - 1e-4), 0.5)
    cal_method = min(cal_metrics, key=lambda m: (cal_metrics[m]["brier_score"], cal_metrics[m]["expected_calibration_error"]))
    try:
        from sklearn.frozen import FrozenEstimator

        calibrator = CalibratedClassifierCV(FrozenEstimator(fitted[selected]), method=cal_method)
    except ImportError:
        calibrator = CalibratedClassifierCV(fitted[selected], method=cal_method, cv="prefit")
    calibrator.fit(Xval, yval)
    test_proba = np.clip(calibrator.predict_proba(Xte)[:, 1], 1e-4, 1 - 1e-4)
    test_metrics = classification_metrics(yte, test_proba, 0.5)

    # --- scale / domain-shift demonstration on MyCreditLens-scale inputs -----
    mean = Xtr.mean(axis=0)
    std = np.maximum(Xtr.std(axis=0), 1e-6)
    train_dist = np.sqrt(np.mean(((Xtr - mean) / std) ** 2, axis=1))
    ood_threshold = float(np.quantile(train_dist, 0.99))
    mcl_examples = pd.DataFrame(
        [
            {"customer_age": 30, "customer_income": 60000, "employment_duration": 5, "loan_amnt": 10000, "loan_percent_income": 10000 / 60000, "home_ownership": "RENT"},
            {"customer_age": 45, "customer_income": 108000, "employment_duration": 12, "loan_amnt": 20000, "loan_percent_income": 20000 / 108000, "home_ownership": "OWN"},
        ]
    )
    mcl_x = np.asarray(pre.transform(mcl_examples[FEATURES]), dtype=float)
    mcl_dist = np.sqrt(np.mean(((mcl_x - mean) / std) ** 2, axis=1))
    ood_flags = (mcl_dist > ood_threshold).tolist()

    # Fraction of Home Credit loans within MyCreditLens loan range (5k-25k).
    in_range = float(((frame["loan_amnt"] >= 5000) & (frame["loan_amnt"] <= 25000)).mean())

    results = {
        "dataset": "home_credit_default_risk (application_train, application-only)",
        "rows_used": int(len(frame)),
        "features": FEATURES,
        "excluded": EXCLUDED,
        "class_balance": {str(k): float(v) for k, v in pd.Series(y).value_counts(normalize=True).items()},
        "selected_model": selected,
        "calibration_method": cal_method,
        "validation_metrics": val_metrics,
        "calibration_metrics": cal_metrics,
        "test_metrics": test_metrics,
        "scale_demo": {
            "homecredit_loan_median": float(frame["loan_amnt"].median()),
            "homecredit_income_median": float(frame["customer_income"].median()),
            "fraction_homecredit_loans_in_mcl_range_5k_25k": in_range,
            "ood_threshold_p99": ood_threshold,
            "mycreditlens_example_ood_distances": [round(float(d), 3) for d in mcl_dist],
            "mycreditlens_examples_flagged_ood": ood_flags,
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "challenger_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({
        "selected": selected,
        "calibration": cal_method,
        "test_roc_auc": round(test_metrics["roc_auc"], 4),
        "test_pr_auc": round(test_metrics["pr_auc"], 4),
        "test_brier": round(test_metrics["brier_score"], 4),
        "test_ece": round(test_metrics["expected_calibration_error"], 4),
        "homecredit_loan_median": results["scale_demo"]["homecredit_loan_median"],
        "fraction_loans_in_mcl_range": round(in_range, 4),
        "mcl_examples_ood_distance": results["scale_demo"]["mycreditlens_example_ood_distances"],
        "mcl_examples_flagged_ood": ood_flags,
        "ood_threshold_p99": round(ood_threshold, 3),
    }, indent=2))


if __name__ == "__main__":
    main()
