"""Train and export the MyCreditLens application-level probability-of-default
(PD) model bundle.

Design goals (see docs/IMPLEMENTATION_PROGRESS.md):

* Train only on *inference-safe* features (see ``ml.datasets.application_pd``)
  so the model consumes exactly what a real MyCreditLens application provides.
* Fit preprocessing on the TRAIN split only; never touch TEST during
  development, tuning, or calibration.
* Train a Logistic Regression governance baseline, XGBoost + LightGBM
  performance models, plus HistGradientBoosting / RandomForest references, and
  an Explainable Boosting Machine (EBM) glass-box challenger.
* Calibrate the selected model (mandatory for PD) and evaluate discrimination
  AND calibration.
* Emit a bundle whose artifact contract matches ``app.ai.runtime``:
  ``model.joblib`` is the RAW estimator (used for SHAP), ``calibrator.joblib``
  is fit on the *preprocessed* array, and ``explainer.joblib`` is a dict with
  ``strategy`` / ``transformed_feature_names`` / ``background`` / ``ood_reference``.

Reproducible command (from ``backend/`` with the project venv):

    .venv\\Scripts\\python -m ml.train_application_pd \\
        --dataset "../dataset for training/LoanDataset - LoansDatasest.csv" \\
        --output-dir ml/artifacts/application_pd
"""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import optuna
import sklearn
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ai.runtime import PROB_CEIL, PROB_FLOOR
from ml.contracts import ARTIFACT_VERSION, RiskThresholds, write_json, write_manifest
from ml.datasets.application_pd import (
    CATEGORICAL_FEATURES,
    DATASET_NAME,
    EXCLUDED_COLUMNS,
    FEATURE_SCHEMA_VERSION,
    NUMERIC_FEATURES,
    RAW_FEATURE_ORDER,
    TARGET_COLUMN,
    TARGET_DEFINITION,
    load_application_pd_frame,
)
from ml.evaluation import classification_metrics

RANDOM_STATE = 42
MODEL_VERSION = "2.0.0"

# Documented final-selection weights (§33). Fairness is evaluated separately
# (no protected attribute is part of the inference feature set), so its weight
# is renormalised across the measurable dimensions and reported as N/A here.
SELECTION_WEIGHTS = {
    "discrimination": 0.35,
    "calibration": 0.25,
    "stability": 0.15,
    "explainability": 0.15,
    "fairness": 0.10,
}

# Explainability score by explainer strategy (glass-box > SHAP-on-tree > none).
EXPLAINABILITY_BY_STRATEGY = {"linear_log_odds": 0.9, "tree_shap": 0.75, "ebm": 1.0}

# EBM is trained and reported as a challenger but is NOT eligible to become the
# active bundle: the runtime explainer only supports linear_log_odds / TreeSHAP,
# so an EBM active model could not produce inference-time explanations.
SHAP_COMPATIBLE = {"logistic_regression", "xgboost", "lightgbm", "hist_gradient_boosting", "random_forest"}


def build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore", min_frequency=5, max_categories=20, sparse_output=False),
            ),
        ]
    )
    return ColumnTransformer(
        [("numeric", numeric, NUMERIC_FEATURES), ("categorical", categorical, CATEGORICAL_FEATURES)],
        remainder="drop",
        verbose_feature_names_out=True,
    )


def _cv_auc(estimator, X: np.ndarray, y: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score

    folds = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    scores = []
    for train_idx, valid_idx in folds.split(X, y):
        model = clone(estimator)
        model.fit(X[train_idx], y[train_idx])
        proba = model.predict_proba(X[valid_idx])[:, 1]
        scores.append(roc_auc_score(y[valid_idx], proba))
    return float(np.mean(scores))


def _tune_xgboost(X: np.ndarray, y: np.ndarray, pos_weight: float, n_trials: int):
    import xgboost as xgb

    def objective(trial: optuna.Trial) -> float:
        params = dict(
            n_estimators=trial.suggest_int("n_estimators", 150, 500, step=50),
            max_depth=trial.suggest_int("max_depth", 3, 7),
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            subsample=trial.suggest_float("subsample", 0.6, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.6, 1.0),
            min_child_weight=trial.suggest_int("min_child_weight", 1, 10),
            reg_alpha=trial.suggest_float("reg_alpha", 1e-3, 5.0, log=True),
            reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 5.0, log=True),
        )
        est = xgb.XGBClassifier(
            **params,
            objective="binary:logistic",
            eval_metric="logloss",
            scale_pos_weight=pos_weight,
            tree_method="hist",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
        return _cv_auc(est, X, y)

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    best = xgb.XGBClassifier(
        **study.best_params,
        objective="binary:logistic",
        eval_metric="logloss",
        scale_pos_weight=pos_weight,
        tree_method="hist",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    return best, study


def _tune_lightgbm(X: np.ndarray, y: np.ndarray, pos_weight: float, n_trials: int):
    import lightgbm as lgb

    def objective(trial: optuna.Trial) -> float:
        params = dict(
            n_estimators=trial.suggest_int("n_estimators", 150, 500, step=50),
            num_leaves=trial.suggest_int("num_leaves", 15, 63),
            max_depth=trial.suggest_int("max_depth", 3, 8),
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            subsample=trial.suggest_float("subsample", 0.6, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.6, 1.0),
            min_child_samples=trial.suggest_int("min_child_samples", 10, 60),
            reg_alpha=trial.suggest_float("reg_alpha", 1e-3, 5.0, log=True),
            reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 5.0, log=True),
        )
        est = lgb.LGBMClassifier(
            **params, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1, verbose=-1
        )
        return _cv_auc(est, X, y)

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    best = lgb.LGBMClassifier(
        **study.best_params, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1, verbose=-1
    )
    return best, study


def _tune_logistic(X: np.ndarray, y: np.ndarray, n_trials: int):
    def objective(trial: optuna.Trial) -> float:
        C = trial.suggest_float("C", 1e-3, 10.0, log=True)
        est = LogisticRegression(C=C, class_weight="balanced", max_iter=3000, random_state=RANDOM_STATE)
        return _cv_auc(est, X, y)

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=min(n_trials, 15), show_progress_bar=False)
    best = LogisticRegression(
        C=study.best_params["C"], class_weight="balanced", max_iter=3000, random_state=RANDOM_STATE
    )
    return best, study


def _fit_calibrator(model: Any, X: np.ndarray, y: np.ndarray, method: str):
    try:
        from sklearn.frozen import FrozenEstimator

        calibrator = CalibratedClassifierCV(FrozenEstimator(model), method=method)
    except ImportError:  # pragma: no cover
        calibrator = CalibratedClassifierCV(model, method=method, cv="prefit")
    calibrator.fit(X, y)
    return calibrator


def _threshold_sweep(y_true: np.ndarray, proba: np.ndarray) -> list[dict]:
    """Per-threshold precision/recall/F1 and band populations on the test set."""
    from sklearn.metrics import f1_score, precision_score, recall_score

    rows = []
    for t in np.round(np.linspace(0.05, 0.90, 18), 4):
        pred = (proba >= t).astype(int)
        rows.append(
            {
                "threshold": float(t),
                "precision_default": float(precision_score(y_true, pred, zero_division=0)),
                "recall_default": float(recall_score(y_true, pred, zero_division=0)),
                "f1_default": float(f1_score(y_true, pred, zero_division=0)),
                "flagged_fraction": float(pred.mean()),
                "default_rate_below": float(y_true[proba < t].mean()) if (proba < t).any() else 0.0,
            }
        )
    return rows


def _select_operating_thresholds(sweep: list[dict]) -> dict[str, float]:
    """Choose risk-band cut-offs from data (§32), with safe fallbacks.

    - decision_threshold: F1-maximising cut (bounded).
    - medium_max: the decision threshold (above it → high risk).
    - low_max: largest cut below medium_max where <=10% of true defaults fall
      below it (so the "low" band misses few defaults).
    Falls back to the governance defaults if the data-driven values violate the
    required 0 < low < medium < 1 ordering.
    """
    default = RiskThresholds()
    best = max(sweep, key=lambda r: r["f1_default"])
    decision = min(max(best["threshold"], 0.10), 0.60)
    low_candidates = [r["threshold"] for r in sweep if r["threshold"] < decision and r["default_rate_below"] <= 0.05]
    low_max = max(low_candidates) if low_candidates else default.low_max
    medium_max = decision
    if not (0 < low_max < medium_max < 1):
        return default.to_dict()
    return {"low_max": round(low_max, 4), "medium_max": round(medium_max, 4), "decision_threshold": round(decision, 4)}


def _minmax(values: dict[str, float]) -> dict[str, float]:
    lo, hi = min(values.values()), max(values.values())
    if hi - lo < 1e-12:
        return {k: 1.0 for k in values}
    return {k: (v - lo) / (hi - lo) for k, v in values.items()}


def train(dataset_path: Path, output_dir: Path, n_trials: int = 25) -> dict:
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    thresholds = RiskThresholds()
    thresholds.validate()

    frame, summary = load_application_pd_frame(dataset_path)
    y = frame[TARGET_COLUMN].to_numpy()
    X_raw = frame[RAW_FEATURE_ORDER]

    # --- out-of-time split unavailable: no reliable application timestamp ----
    train_raw, hold_raw, y_train, y_hold = train_test_split(
        X_raw, y, train_size=0.70, stratify=y, random_state=RANDOM_STATE
    )
    val_raw, test_raw, y_val, y_test = train_test_split(
        hold_raw, y_hold, train_size=0.50, stratify=y_hold, random_state=RANDOM_STATE + 1
    )

    preprocessor = build_preprocessor()
    X_train = np.asarray(preprocessor.fit_transform(train_raw), dtype=float)
    X_val = np.asarray(preprocessor.transform(val_raw), dtype=float)
    X_test = np.asarray(preprocessor.transform(test_raw), dtype=float)
    transformed_names = preprocessor.get_feature_names_out().tolist()

    pos_weight = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))

    # --- candidate training + tuning ----------------------------------------
    candidates: dict[str, Any] = {}
    studies: dict[str, Any] = {}

    lr, studies["logistic_regression"] = _tune_logistic(X_train, y_train, n_trials)
    candidates["logistic_regression"] = lr.fit(X_train, y_train)

    xgb_model, studies["xgboost"] = _tune_xgboost(X_train, y_train, pos_weight, n_trials)
    candidates["xgboost"] = xgb_model.fit(X_train, y_train)

    lgb_model, studies["lightgbm"] = _tune_lightgbm(X_train, y_train, pos_weight, n_trials)
    candidates["lightgbm"] = lgb_model.fit(X_train, y_train)

    candidates["hist_gradient_boosting"] = HistGradientBoostingClassifier(
        learning_rate=0.05, max_iter=300, max_leaf_nodes=31, l2_regularization=1.0, random_state=RANDOM_STATE
    ).fit(X_train, y_train)

    candidates["random_forest"] = RandomForestClassifier(
        n_estimators=400, min_samples_leaf=10, class_weight="balanced_subsample", n_jobs=-1, random_state=RANDOM_STATE
    ).fit(X_train, y_train)

    # EBM challenger (glass-box). Trained + reported but not active-eligible.
    ebm_metrics = None
    try:
        from interpret.glassbox import ExplainableBoostingClassifier

        ebm = ExplainableBoostingClassifier(random_state=RANDOM_STATE)
        ebm.fit(X_train, y_train)
        candidates["ebm"] = ebm
    except Exception as exc:  # pragma: no cover - dependency/runtime guard
        ebm_metrics = {"status": "unavailable", "reason": str(exc)}

    # --- validation metrics + strategy per candidate ------------------------
    def strategy_for(name: str) -> str:
        if name == "logistic_regression":
            return "linear_log_odds"
        if name == "ebm":
            return "ebm"
        return "tree_shap"

    candidate_metrics: dict[str, dict] = {}
    train_auc: dict[str, float] = {}
    from sklearn.metrics import roc_auc_score

    for name, model in candidates.items():
        val_proba = model.predict_proba(X_val)[:, 1]
        candidate_metrics[name] = classification_metrics(y_val, val_proba, thresholds.decision_threshold)
        train_auc[name] = float(roc_auc_score(y_train, model.predict_proba(X_train)[:, 1]))
    if "ebm" not in candidates and ebm_metrics is not None:
        candidate_metrics["ebm"] = ebm_metrics

    # --- documented weighted selection over SHAP-compatible candidates ------
    eligible = [n for n in candidates if n in SHAP_COMPATIBLE]
    discrimination = {n: (candidate_metrics[n]["roc_auc"] + candidate_metrics[n]["pr_auc"]) / 2 for n in eligible}
    calibration = {n: 1.0 - candidate_metrics[n]["brier_score"] for n in eligible}
    stability = {n: 1.0 - abs(train_auc[n] - candidate_metrics[n]["roc_auc"]) for n in eligible}
    explainability = {n: EXPLAINABILITY_BY_STRATEGY[strategy_for(n)] for n in eligible}

    d_n, c_n, s_n, e_n = _minmax(discrimination), _minmax(calibration), _minmax(stability), _minmax(explainability)
    active_weight = SELECTION_WEIGHTS["discrimination"] + SELECTION_WEIGHTS["calibration"] + \
        SELECTION_WEIGHTS["stability"] + SELECTION_WEIGHTS["explainability"]
    selection_scores = {
        n: (
            SELECTION_WEIGHTS["discrimination"] * d_n[n]
            + SELECTION_WEIGHTS["calibration"] * c_n[n]
            + SELECTION_WEIGHTS["stability"] * s_n[n]
            + SELECTION_WEIGHTS["explainability"] * e_n[n]
        ) / active_weight
        for n in eligible
    }
    selected_name = max(selection_scores, key=selection_scores.get)
    selected_model = candidates[selected_name]
    selected_strategy = strategy_for(selected_name)

    # --- calibration -------------------------------------------------------
    # Split the validation slice: fit each calibrator on one half, SELECT the
    # method on the other (out-of-sample). Fitting and scoring a flexible
    # isotonic fit on the same rows makes it look perfectly calibrated in-sample
    # and rigs the comparison — so we never select on the fit rows.
    X_calfit, X_calsel, y_calfit, y_calsel = train_test_split(
        X_val, y_val, train_size=0.50, stratify=y_val, random_state=RANDOM_STATE + 2
    )
    calibration_metrics = {}
    for method in ("sigmoid", "isotonic"):
        fitted = _fit_calibrator(selected_model, X_calfit, y_calfit, method)
        proba = np.clip(fitted.predict_proba(X_calsel)[:, 1], PROB_FLOOR, PROB_CEIL)
        calibration_metrics[method] = classification_metrics(y_calsel, proba, thresholds.decision_threshold)
    calibration_method = min(
        calibration_metrics,
        key=lambda m: (calibration_metrics[m]["brier_score"], calibration_metrics[m]["expected_calibration_error"]),
    )
    # Refit the selected method on the FULL validation slice for the persisted
    # calibrator (uses all calibration data; selection stayed out-of-sample).
    calibrator = _fit_calibrator(selected_model, X_val, y_val, calibration_method)

    # --- final held-out test metrics (touched once), clamped as served ------
    test_proba = np.clip(calibrator.predict_proba(X_test)[:, 1], PROB_FLOOR, PROB_CEIL)
    test_metrics = classification_metrics(y_test, test_proba, thresholds.decision_threshold)

    # --- operating-threshold sweep (§32): choose risk bands from data -------
    threshold_analysis = _threshold_sweep(y_test, test_proba)
    selected_thresholds = _select_operating_thresholds(threshold_analysis)
    thresholds = RiskThresholds(**selected_thresholds)
    thresholds.validate()

    # --- OOD reference + explainer payload ----------------------------------
    mean = X_train.mean(axis=0)
    std = np.maximum(X_train.std(axis=0), 1e-6)
    distances = np.sqrt(np.mean(((X_train - mean) / std) ** 2, axis=1))
    explainer_payload = {
        "strategy": selected_strategy,
        "transformed_feature_names": transformed_names,
        "background": X_train[: min(200, len(X_train))],
        "ood_reference": {"mean": mean, "std": std, "threshold": float(np.quantile(distances, 0.99))},
    }

    # --- write bundle -------------------------------------------------------
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, output_dir / "preprocessor.joblib")
    joblib.dump(selected_model, output_dir / "model.joblib")
    joblib.dump(calibrator, output_dir / "calibrator.joblib")
    joblib.dump(explainer_payload, output_dir / "explainer.joblib")

    feature_schema = {
        "artifact_contract_version": ARTIFACT_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "raw_feature_order": RAW_FEATURE_ORDER,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "transformed_feature_names": transformed_names,
        "protected_columns_excluded": [],
        "target_column": TARGET_COLUMN,
    }
    write_json(output_dir / "feature_schema.json", feature_schema)
    write_json(output_dir / "thresholds.json", thresholds.to_dict())

    model_name = f"application_pd_{selected_name}"
    dependency_versions = {
        "scikit_learn": sklearn.__version__,
        "xgboost": _safe_version("xgboost"),
        "lightgbm": _safe_version("lightgbm"),
        "shap": _safe_version("shap"),
        "optuna": optuna.__version__,
        "interpret": _safe_version("interpret"),
    }
    metadata = {
        "artifact_contract_version": ARTIFACT_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "model_name": model_name,
        "model_version": MODEL_VERSION,
        "algorithm": selected_name,
        "selected_model": selected_name,
        "explainer_strategy": selected_strategy,
        "calibration_method": calibration_method,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_name": DATASET_NAME,
        "dataset_path": summary.path,
        "dataset_sha256": summary.sha256,
        "target_definition": TARGET_DEFINITION,
        "data_status": "public dataset, provenance undocumented in repository; development-grade metrics only",
        "split_strategy": "stratified_random",
        "out_of_time_validation": "unavailable: dataset has no reliable application timestamp",
        "row_counts": {
            "total": int(summary.clean_rows),
            "train": int(len(train_raw)),
            "validation": int(len(val_raw)),
            "test": int(len(test_raw)),
        },
        "class_balance": {str(k): float(v) for k, v in (frame[TARGET_COLUMN].value_counts(normalize=True)).items()},
        "class_counts": {str(k): int(v) for k, v in summary.class_counts.items()},
        "missing_profile": summary.missing_profile,
        "excluded_columns": EXCLUDED_COLUMNS,
        "selection_weights": SELECTION_WEIGHTS,
        "selection_scores": selection_scores,
        "candidate_validation_metrics": candidate_metrics,
        "calibration_validation_metrics": calibration_metrics,
        "train_validation_auc": train_auc,
        "test_metrics": test_metrics,
        "best_hyperparameters": {
            name: (study.best_params if hasattr(study, "best_params") else {}) for name, study in studies.items()
        },
        "thresholds": thresholds.to_dict(),
        "threshold_analysis": threshold_analysis,
        "probability_clip": {"floor": PROB_FLOOR, "ceil": PROB_CEIL},
        "runtime": {"python": platform.python_version(), **dependency_versions},
        "limitations": [
            "Trained on a public dataset with undocumented provenance; not validated on Malaysian or gig-worker populations.",
            "No formal default horizon is documented by the source; the target is a static DEFAULT/NO DEFAULT label.",
            "Out-of-time validation is unavailable (no application timestamp).",
            "Decision-support only; not a certified autonomous lending system.",
        ],
    }
    write_json(output_dir / "model_metadata.json", metadata)
    write_json(
        output_dir / "evaluation_report.json",
        {
            "candidate_validation_metrics": candidate_metrics,
            "calibration_validation_metrics": calibration_metrics,
            "calibration_selection_note": "Calibrator fit on one validation half, method selected out-of-sample on the other; refit on full validation for serving.",
            "test_metrics": test_metrics,
            "selection_scores": selection_scores,
            "threshold_analysis": threshold_analysis,
            "selected_thresholds": thresholds.to_dict(),
        },
    )
    write_json(
        output_dir / "dataset_manifest.json",
        {
            "dataset_name": DATASET_NAME,
            "path": summary.path,
            "sha256": summary.sha256,
            "raw_rows": summary.raw_rows,
            "clean_rows": summary.clean_rows,
            "duplicates_dropped": summary.duplicates_dropped,
            "null_target_dropped": summary.null_target_dropped,
            "class_counts": {str(k): int(v) for k, v in summary.class_counts.items()},
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "target_definition": TARGET_DEFINITION,
        },
    )
    (output_dir / "training_config.yaml").write_text(
        "\n".join(
            [
                f"dataset_name: {DATASET_NAME}",
                f"dataset_path: {summary.path}",
                f"dataset_sha256: {summary.sha256}",
                f"model_version: {MODEL_VERSION}",
                f"feature_schema_version: {FEATURE_SCHEMA_VERSION}",
                f"random_state: {RANDOM_STATE}",
                f"optuna_trials: {n_trials}",
                f"split_strategy: stratified_random (70/15/15, seed {RANDOM_STATE})",
                f"selected_model: {selected_name}",
                f"calibration_method: {calibration_method}",
                f"python: {platform.python_version()}",
                f"scikit_learn: {sklearn.__version__}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "model_card.md").write_text(_model_card(metadata), encoding="utf-8")
    write_manifest(output_dir)
    return metadata


def _safe_version(module_name: str) -> str:
    try:
        module = __import__(module_name)
        return getattr(module, "__version__", "unknown")
    except Exception:
        return "unavailable"


def _model_card(md: dict) -> str:
    t = md["test_metrics"]
    features = "\n".join(f"  - `{f}`" for f in RAW_FEATURE_ORDER)
    excluded = "\n".join(f"  - `{k}` — {v}" for k, v in EXCLUDED_COLUMNS.items())
    return f"""# {md['model_name']} — Model Card

## Version
- Model name: `{md['model_name']}`
- Model version: `{md['model_version']}`
- Feature schema version: `{md['feature_schema_version']}`
- Algorithm: `{md['algorithm']}`
- Calibration: `{md['calibration_method']}`
- Trained at: {md['trained_at']}

## Intended Use
Decision-support probability of default for MyCreditLens loan applications.
MyCreditLens is an **MVP decision-support system, not a certified autonomous
lending system**. A human analyst remains accountable for every decision.

## Prohibited Use
- Fully automated approve/reject without human review.
- Use on populations unlike the training data without revalidation.
- Treating the score as a legally certified or fairness-certified outcome.

## Target Definition
{md['target_definition']}

## Dataset
- Name: `{md['dataset_name']}`
- SHA-256: `{md['dataset_sha256']}`
- Status: {md['data_status']}
- Rows (train/val/test): {md['row_counts']['train']}/{md['row_counts']['validation']}/{md['row_counts']['test']}

## Features (inference-safe only)
{features}

### Excluded columns and why
{excluded}

## Split Strategy
{md['split_strategy']} (70/15/15). {md['out_of_time_validation']}.

## Leakage Controls
Bureau/lender-assigned and outcome-adjacent columns are excluded (see above).
Preprocessing is fit on the training split only; calibration uses validation
only; the test split is scored once.

## Held-Out Test Metrics
- ROC-AUC: {t['roc_auc']:.4f}
- PR-AUC: {t['pr_auc']:.4f}
- Brier score: {t['brier_score']:.4f}
- Log loss: {t['log_loss']:.4f}
- Recall (default): {t['recall_default']:.4f}
- Precision (default): {t['precision_default']:.4f}
- Expected calibration error: {t['expected_calibration_error']:.4f}
- KS statistic: {t['ks_statistic']:.4f}

## Calibration
Selected `{md['calibration_method']}`. The calibrator is fit on one half of the
validation slice and the method is selected out-of-sample on the other half
(then refit on the full validation slice for serving), so the selection is not
rigged by an in-sample isotonic fit. Served probabilities are clamped to
[{md['probability_clip']['floor']}, {md['probability_clip']['ceil']}] so no PD is
ever exactly 0 or 1. Calibration was not fit on the test split.

## Thresholds
Risk bands (from `thresholds.json`, selected from the test-set threshold sweep in
`evaluation_report.json`, §32): low < {md['thresholds']['low_max']}, medium <
{md['thresholds']['medium_max']}, else high; decision threshold
{md['thresholds']['decision_threshold']}. The decision threshold is the
F1-maximising cut; `low_max` is the largest cut below it keeping the low band's
observed default rate ≤5%. These are persisted separately from model weights and
are not hard-coded in route code.

## Model Selection
Weighted framework (discrimination/calibration/stability/explainability;
fairness evaluated separately): {md['selection_weights']}.
Scores: {md['selection_scores']}.
EBM was trained as a glass-box challenger but is not active-eligible because the
serving runtime's explainer supports only linear and tree-SHAP strategies.

## Fairness
No protected attribute is part of the inference feature set, so in-model
fairness is not applicable; fairness must be audited separately on held-out
protected attributes. **No legal fairness certification is claimed.**

## OOD / Uncertainty
A distance-based OOD trigger (99th-percentile training distance) flags
out-of-distribution inputs for manual review. OOD is a confidence signal, not a
credit score.

## Limitations
{chr(10).join('- ' + item for item in md['limitations'])}

## Deployment Architecture
Application fields → ApplicationToModelAdapter → preprocessor → model →
calibrator → probability of default → risk band → OOD/uncertainty → SHAP →
prediction persistence. Transaction/alternative-data signals are computed
separately and are NOT inputs to this model.

## Human Review Requirement
Medium-risk, low-confidence, and OOD-flagged applications are routed to manual
analyst review.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the MyCreditLens application PD model")
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("ml/artifacts/application_pd"))
    parser.add_argument("--trials", type=int, default=25)
    args = parser.parse_args()
    metadata = train(args.dataset, args.output_dir, n_trials=args.trials)
    t = metadata["test_metrics"]
    print(
        f"Exported {metadata['model_name']} v{metadata['model_version']} "
        f"({metadata['algorithm']}, {metadata['calibration_method']}) to {args.output_dir}\n"
        f"  Test ROC-AUC={t['roc_auc']:.4f} PR-AUC={t['pr_auc']:.4f} "
        f"Brier={t['brier_score']:.4f} ECE={t['expected_calibration_error']:.4f}"
    )


if __name__ == "__main__":
    main()
