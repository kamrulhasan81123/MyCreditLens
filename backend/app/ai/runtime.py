from __future__ import annotations

import json
import math
from functools import lru_cache
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.ai.shap_explainer import ShapExplainer
from ml.contracts import RiskThresholds, verify_manifest


# A calibrated PD must never be exactly 0 or 1 — a credit model asserting that
# default is impossible or certain is indefensible, and isotonic calibration
# clips its extreme bins to hard 0/1. Clamp to a small floor/ceiling.
PROB_FLOOR = 1e-4
PROB_CEIL = 1.0 - PROB_FLOOR


class ArtifactUnavailableError(RuntimeError):
    pass


class FeatureSchemaError(ValueError):
    pass


@dataclass(frozen=True)
class InferenceResult:
    probability_of_default: float
    risk_band: str
    confidence: float
    is_ood: bool
    ood_score: float
    model_version: str
    model_name: str
    feature_values: dict[str, Any]
    contributions: list[dict[str, Any]]
    plain_language_explanation: str
    raw_probability: float = 0.0
    calibrated_probability: float = 0.0
    uncertainty: float = 0.0
    feature_schema_version: str | None = None


class CreditModelRuntime:
    """Immutable, artifact-only inference runtime."""

    def __init__(self, artifact_dir: str | Path):
        self.artifact_dir = Path(artifact_dir)
        try:
            verify_manifest(self.artifact_dir)
            self.preprocessor = joblib.load(self.artifact_dir / "preprocessor.joblib")
            self.model = joblib.load(self.artifact_dir / "model.joblib")
            self.calibrator = joblib.load(self.artifact_dir / "calibrator.joblib")
            self.explainer = joblib.load(self.artifact_dir / "explainer.joblib")
            self.schema = self._read_json("feature_schema.json")
            self.metadata = self._read_json("model_metadata.json")
            threshold_payload = self._read_json("thresholds.json")
            self.thresholds = RiskThresholds(**threshold_payload)
            self.thresholds.validate()
        except Exception as exc:
            raise ArtifactUnavailableError(f"Model artifact bundle could not be loaded: {exc}") from exc

    def _read_json(self, name: str) -> dict:
        return json.loads((self.artifact_dir / name).read_text(encoding="utf-8"))

    @property
    def model_version(self) -> str:
        return str(self.metadata["model_version"])

    @property
    def model_name(self) -> str:
        return str(self.metadata["model_name"])

    def _frame(self, features: dict[str, Any]) -> pd.DataFrame:
        required = list(self.schema["raw_feature_order"])
        missing = [name for name in required if name not in features]
        if missing:
            raise FeatureSchemaError(
                "Inference features do not match the trained schema. Missing: " + ", ".join(missing)
            )
        payload = {name: features[name] for name in required}
        for name in self.schema.get("numeric_features", []):
            value = payload[name]
            if value is not None and not (isinstance(value, (int, float, np.number)) and math.isfinite(float(value))):
                raise FeatureSchemaError(f"Numeric feature is not finite: {name}")
        return pd.DataFrame([payload], columns=required)

    @property
    def feature_schema_version(self) -> str | None:
        return self.schema.get("feature_schema_version")

    def predict(self, features: dict[str, Any], *, include_explanation: bool = True) -> InferenceResult:
        frame = self._frame(features)
        transformed = np.asarray(self.preprocessor.transform(frame), dtype=float)
        raw_probability = float(np.clip(self.model.predict_proba(transformed)[0, 1], PROB_FLOOR, PROB_CEIL))
        probability = float(self.calibrator.predict_proba(transformed)[0, 1])
        probability = float(np.clip(probability, PROB_FLOOR, PROB_CEIL))
        ood_score, is_ood = self._ood(transformed[0])
        contributions = self._contributions(transformed[0]) if include_explanation else []
        completeness = sum(value is not None for value in frame.iloc[0]) / max(frame.shape[1], 1)
        distribution_confidence = 1.0 - 0.25 * min(ood_score, 1.0) - 0.75 * max(ood_score - 1.0, 0.0)
        confidence = float(np.clip(completeness * distribution_confidence, 0.0, 1.0))
        explanation = (
            ShapExplainer.controlled_summary(contributions, probability)
            if include_explanation
            else "Explanation generation was not requested for this scenario evaluation."
        )
        return InferenceResult(
            probability_of_default=probability,
            risk_band=self.thresholds.band(probability),
            confidence=confidence,
            is_ood=is_ood,
            ood_score=ood_score,
            model_version=self.model_version,
            model_name=self.model_name,
            feature_values=frame.iloc[0].to_dict(),
            contributions=contributions,
            plain_language_explanation=explanation,
            raw_probability=raw_probability,
            calibrated_probability=probability,
            uncertainty=float(np.clip(1.0 - confidence, 0.0, 1.0)),
            feature_schema_version=self.feature_schema_version,
        )

    def _ood(self, transformed: np.ndarray) -> tuple[float, bool]:
        reference = self.explainer["ood_reference"]
        mean = np.asarray(reference["mean"], dtype=float)
        std = np.asarray(reference["std"], dtype=float)
        raw_distance = float(np.sqrt(np.mean(((transformed - mean) / std) ** 2)))
        threshold = max(float(reference["threshold"]), 1e-6)
        normalized = raw_distance / threshold
        return round(normalized, 6), raw_distance > threshold

    def _contributions(self, transformed: np.ndarray) -> list[dict[str, Any]]:
        names = list(self.explainer["transformed_feature_names"])
        strategy = self.explainer["strategy"]
        if strategy == "linear_log_odds" and hasattr(self.model, "coef_"):
            values = transformed * np.asarray(self.model.coef_[0], dtype=float)
        else:
            try:
                import shap

                tree_explainer = shap.TreeExplainer(self.model)
                shap_values = tree_explainer.shap_values(transformed.reshape(1, -1))
                if isinstance(shap_values, list):
                    shap_values = shap_values[-1]
                array = np.asarray(shap_values)
                if array.ndim == 3:
                    array = array[0, :, -1]
                elif array.ndim == 2:
                    array = array[0]
                values = array.reshape(-1)
            except Exception as exc:
                raise ArtifactUnavailableError(f"Real model explanations could not be generated: {exc}") from exc
        contributions = [
            {
                "feature": name,
                "label": ShapExplainer.label(name),
                "value": float(transformed[index]),
                "contribution": float(values[index]),
                "direction": "increases_risk" if values[index] > 0 else "reduces_risk",
            }
            for index, name in enumerate(names)
        ]
        contributions.sort(key=lambda item: abs(item["contribution"]), reverse=True)
        return contributions[:10]


@lru_cache(maxsize=4)
def _cached_runtime(path: str, manifest_mtime_ns: int) -> CreditModelRuntime:
    return CreditModelRuntime(path)


def load_credit_runtime(artifact_dir: str | Path) -> CreditModelRuntime:
    path = Path(artifact_dir).resolve()
    manifest = path / "manifest.json"
    if not manifest.is_file():
        raise ArtifactUnavailableError("Verified trained model artifacts are not available")
    return _cached_runtime(str(path), manifest.stat().st_mtime_ns)
