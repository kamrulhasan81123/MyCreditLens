from __future__ import annotations

import json
import platform
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.contracts import ARTIFACT_VERSION, RiskThresholds, write_json, write_manifest
from ml.evaluation import classification_metrics


LEAKAGE_PATTERN = re.compile(
    r"(^|_)(target|outcome|default|delinquen|repay|collection|days_past_due|loan_status|future)(_|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TrainingConfig:
    target_column: str
    output_dir: Path
    model_name: str = "MyCreditLensCreditRisk"
    model_version: str = "1.0.0"
    positive_label: int | str = 1
    group_column: str | None = None
    time_column: str | None = None
    protected_columns: tuple[str, ...] = ()
    drop_columns: tuple[str, ...] = ()
    leakage_allowlist: tuple[str, ...] = ()
    random_state: int = 42
    minimum_rows: int = 100
    thresholds: RiskThresholds = field(default_factory=RiskThresholds)
    dataset_name: str = "user_provided"
    target_definition: str = "User-provided binary default outcome"


@dataclass
class DatasetSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


def _validate_and_prepare(frame: pd.DataFrame, config: TrainingConfig) -> tuple[pd.DataFrame, pd.Series]:
    if config.target_column not in frame.columns:
        raise ValueError(f"Target column is missing: {config.target_column}")
    if len(frame) < config.minimum_rows:
        raise ValueError(f"Dataset has {len(frame)} rows; at least {config.minimum_rows} are required")
    if frame.columns.duplicated().any():
        duplicates = frame.columns[frame.columns.duplicated()].tolist()
        raise ValueError(f"Duplicate column names are not allowed: {duplicates}")

    cleaned = frame.drop_duplicates().copy()
    target = (cleaned.pop(config.target_column) == config.positive_label).astype(int)
    counts = target.value_counts()
    if set(counts.index) != {0, 1}:
        raise ValueError("Target must contain both binary classes after positive-label mapping")
    if int(counts.min()) < 20:
        raise ValueError("Each target class must contain at least 20 rows")

    excluded = set(config.drop_columns) | set(config.protected_columns)
    excluded.update(column for column in (config.group_column, config.time_column) if column)
    cleaned = cleaned.drop(columns=[column for column in excluded if column in cleaned], errors="ignore")
    allowlist = {column.lower() for column in config.leakage_allowlist}
    suspicious = [
        column
        for column in cleaned.columns
        if column.lower() not in allowlist and LEAKAGE_PATTERN.search(column.replace(" ", "_"))
    ]
    if suspicious:
        raise ValueError(f"Potential target leakage columns detected: {', '.join(suspicious)}")
    if cleaned.empty:
        raise ValueError("No feature columns remain after exclusions")
    if cleaned.isna().all(axis=0).any():
        empty = cleaned.columns[cleaned.isna().all()].tolist()
        raise ValueError(f"Completely empty feature columns are not allowed: {empty}")
    numeric = cleaned.select_dtypes(include=["number", "bool"])
    if not numeric.empty and np.isinf(numeric.to_numpy(dtype=float)).any():
        raise ValueError("Numeric features contain infinite values")
    categorical = cleaned.select_dtypes(exclude=["number", "bool"])
    identifier_like = [
        column
        for column in categorical
        if cleaned[column].nunique(dropna=True) > 100
        and cleaned[column].nunique(dropna=True) / len(cleaned) > 0.90
    ]
    if identifier_like:
        raise ValueError(
            "Identifier-like high-cardinality columns must be explicitly dropped: " + ", ".join(identifier_like)
        )
    return cleaned, target


def _split_indices(frame: pd.DataFrame, target: pd.Series, config: TrainingConfig) -> DatasetSplit:
    indices = np.arange(len(frame))
    if config.time_column:
        if config.time_column not in frame.columns:
            raise ValueError(f"Time split column is missing: {config.time_column}")
        ordered = np.argsort(pd.to_datetime(frame[config.time_column], errors="raise").to_numpy())
        train_end = int(len(ordered) * 0.70)
        validation_end = int(len(ordered) * 0.85)
        return DatasetSplit(
            pd.DataFrame({"index": ordered[:train_end]}),
            pd.DataFrame({"index": ordered[train_end:validation_end]}),
            pd.DataFrame({"index": ordered[validation_end:]}),
        )
    if config.group_column:
        if config.group_column not in frame.columns:
            raise ValueError(f"Group split column is missing: {config.group_column}")
        groups = frame[config.group_column].astype(str)
        first = GroupShuffleSplit(n_splits=1, train_size=0.70, random_state=config.random_state)
        train_idx, remainder_idx = next(first.split(indices, target, groups))
        second = GroupShuffleSplit(n_splits=1, train_size=0.50, random_state=config.random_state + 1)
        validation_rel, test_rel = next(
            second.split(remainder_idx, target.iloc[remainder_idx], groups.iloc[remainder_idx])
        )
        return DatasetSplit(
            pd.DataFrame({"index": train_idx}),
            pd.DataFrame({"index": remainder_idx[validation_rel]}),
            pd.DataFrame({"index": remainder_idx[test_rel]}),
        )

    train_idx, remainder_idx = train_test_split(
        indices,
        train_size=0.70,
        stratify=target,
        random_state=config.random_state,
    )
    validation_idx, test_idx = train_test_split(
        remainder_idx,
        train_size=0.50,
        stratify=target.iloc[remainder_idx],
        random_state=config.random_state + 1,
    )
    return DatasetSplit(
        pd.DataFrame({"index": train_idx}),
        pd.DataFrame({"index": validation_idx}),
        pd.DataFrame({"index": test_idx}),
    )


def _build_preprocessor(features: pd.DataFrame) -> tuple[ColumnTransformer, list[str], list[str]]:
    numeric = features.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical = [column for column in features.columns if column not in numeric]
    transformers = []
    if numeric:
        transformers.append(
            (
                "numeric",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                numeric,
            )
        )
    if categorical:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OneHotEncoder(
                                handle_unknown="ignore",
                                min_frequency=5,
                                max_categories=100,
                                sparse_output=False,
                            ),
                        ),
                    ]
                ),
                categorical,
            )
        )
    return ColumnTransformer(transformers, remainder="drop", verbose_feature_names_out=True), numeric, categorical


def _candidate_models(random_state: int) -> dict[str, Any]:
    return {
        "logistic_regression": LogisticRegression(
            class_weight="balanced",
            max_iter=2000,
            random_state=random_state,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=400,
            min_samples_leaf=10,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=random_state,
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_iter=300,
            max_leaf_nodes=31,
            l2_regularization=1.0,
            random_state=random_state,
        ),
    }


def _fit_calibrator(model: Any, features: np.ndarray, labels: np.ndarray, method: str):
    try:
        from sklearn.frozen import FrozenEstimator

        calibrator = CalibratedClassifierCV(FrozenEstimator(model), method=method)
    except ImportError:
        calibrator = CalibratedClassifierCV(model, method=method, cv="prefit")
    calibrator.fit(features, labels)
    return calibrator


def _model_card(metadata: dict, config: TrainingConfig) -> str:
    metrics = metadata["test_metrics"]
    return f"""# {config.model_name} Model Card

## Version

- Model version: `{config.model_version}`
- Artifact contract: `{ARTIFACT_VERSION}`
- Dataset: `{config.dataset_name}`
- Target: {config.target_definition}

## Intended Use

Decision-support probability of default for trained feature-compatible applications. The model must not make autonomous lending decisions. Analysts remain accountable for final decisions.

## Training Design

- Split strategy: `{metadata['split_strategy']}`
- Selected estimator: `{metadata['selected_model']}`
- Calibration: `{metadata['calibration_method']}`
- Train/validation/test rows: `{metadata['row_counts']['train']}/{metadata['row_counts']['validation']}/{metadata['row_counts']['test']}`

## Held-Out Test Metrics

- ROC-AUC: `{metrics['roc_auc']:.4f}`
- PR-AUC: `{metrics['pr_auc']:.4f}`
- Brier score: `{metrics['brier_score']:.4f}`
- Log loss: `{metrics['log_loss']:.4f}`
- Default recall: `{metrics['recall_default']:.4f}`
- Default precision: `{metrics['precision_default']:.4f}`
- Expected calibration error: `{metrics['expected_calibration_error']:.4f}`
- KS statistic: `{metrics['ks_statistic']:.4f}`

## Limitations

- Metrics apply only to the supplied dataset and split.
- Public datasets do not establish Malaysian, gig-worker, or production-lending validity.
- Synthetic features do not constitute real-world evidence.
- Protected attributes are excluded from model features and require separate fairness evaluation.
- OOD detection is a distance-based review trigger, not proof that a prediction is invalid.
"""


def train_credit_model(frame: pd.DataFrame, config: TrainingConfig) -> dict:
    config.thresholds.validate()
    raw_frame = frame.drop_duplicates().reset_index(drop=True)
    features, target = _validate_and_prepare(raw_frame, config)
    split = _split_indices(raw_frame, target, config)
    train_idx = split.train["index"].to_numpy()
    validation_idx = split.validation["index"].to_numpy()
    test_idx = split.test["index"].to_numpy()
    if any(len(np.unique(target.iloc[idx])) != 2 for idx in (train_idx, validation_idx, test_idx)):
        raise ValueError("Every data split must contain both target classes")

    preprocessor, numeric, categorical = _build_preprocessor(features)
    train_x = preprocessor.fit_transform(features.iloc[train_idx])
    validation_x = preprocessor.transform(features.iloc[validation_idx])
    test_x = preprocessor.transform(features.iloc[test_idx])
    train_y = target.iloc[train_idx].to_numpy()
    validation_y = target.iloc[validation_idx].to_numpy()
    test_y = target.iloc[test_idx].to_numpy()

    candidate_metrics = {}
    fitted_models = {}
    for name, candidate in _candidate_models(config.random_state).items():
        fitted = clone(candidate).fit(train_x, train_y)
        probabilities = fitted.predict_proba(validation_x)[:, 1]
        metrics = classification_metrics(validation_y, probabilities, config.thresholds.decision_threshold)
        candidate_metrics[name] = metrics
        fitted_models[name] = fitted
    selected_name = max(
        candidate_metrics,
        key=lambda name: (
            candidate_metrics[name]["roc_auc"],
            candidate_metrics[name]["pr_auc"],
            -candidate_metrics[name]["brier_score"],
        ),
    )
    selected_model = fitted_models[selected_name]

    calibrators = {}
    calibration_metrics = {}
    for method in ("sigmoid", "isotonic"):
        calibrator = _fit_calibrator(selected_model, validation_x, validation_y, method)
        probabilities = calibrator.predict_proba(validation_x)[:, 1]
        calibrators[method] = calibrator
        calibration_metrics[method] = classification_metrics(
            validation_y, probabilities, config.thresholds.decision_threshold
        )
    calibration_method = min(
        calibration_metrics,
        key=lambda method: (
            calibration_metrics[method]["brier_score"],
            calibration_metrics[method]["expected_calibration_error"],
        ),
    )
    calibrator = calibrators[calibration_method]
    test_probabilities = calibrator.predict_proba(test_x)[:, 1]
    test_metrics = classification_metrics(test_y, test_probabilities, config.thresholds.decision_threshold)

    transformed_names = preprocessor.get_feature_names_out().tolist()
    train_array = np.asarray(train_x, dtype=float)
    transformed_mean = train_array.mean(axis=0)
    transformed_std = np.maximum(train_array.std(axis=0), 1e-6)
    distances = np.sqrt(np.mean(((train_array - transformed_mean) / transformed_std) ** 2, axis=1))
    ood_reference = {
        "mean": transformed_mean,
        "std": transformed_std,
        "threshold": float(np.quantile(distances, 0.99)),
    }
    explainer_payload = {
        "strategy": "linear_log_odds" if selected_name == "logistic_regression" else "tree_shap",
        "transformed_feature_names": transformed_names,
        "background": train_array[: min(200, len(train_array))],
        "ood_reference": ood_reference,
    }

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, output_dir / "preprocessor.joblib")
    joblib.dump(selected_model, output_dir / "model.joblib")
    joblib.dump(calibrator, output_dir / "calibrator.joblib")
    joblib.dump(explainer_payload, output_dir / "explainer.joblib")

    feature_schema = {
        "artifact_contract_version": ARTIFACT_VERSION,
        "raw_feature_order": features.columns.tolist(),
        "numeric_features": numeric,
        "categorical_features": categorical,
        "transformed_feature_names": transformed_names,
        "protected_columns_excluded": list(config.protected_columns),
        "target_column": config.target_column,
    }
    write_json(output_dir / "feature_schema.json", feature_schema)
    write_json(output_dir / "thresholds.json", config.thresholds.to_dict())

    metadata = {
        "artifact_contract_version": ARTIFACT_VERSION,
        "model_name": config.model_name,
        "model_version": config.model_version,
        "selected_model": selected_name,
        "calibration_method": calibration_method,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_name": config.dataset_name,
        "target_definition": config.target_definition,
        "split_strategy": "time" if config.time_column else "group" if config.group_column else "stratified_random",
        "row_counts": {"total": len(features), "train": len(train_idx), "validation": len(validation_idx), "test": len(test_idx)},
        "class_balance": target.value_counts(normalize=True).sort_index().to_dict(),
        "candidate_validation_metrics": candidate_metrics,
        "calibration_validation_metrics": calibration_metrics,
        "test_metrics": test_metrics,
        "training_config": {**asdict(config), "output_dir": str(config.output_dir)},
        "runtime": {"python": platform.python_version(), "scikit_learn": sklearn.__version__},
    }
    write_json(output_dir / "model_metadata.json", metadata)
    (output_dir / "model_card.md").write_text(_model_card(metadata, config), encoding="utf-8")
    write_manifest(output_dir)
    return metadata
