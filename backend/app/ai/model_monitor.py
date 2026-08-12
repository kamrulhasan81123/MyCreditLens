from __future__ import annotations

from typing import Any

import numpy as np

from ml.evaluation import classification_metrics


class ModelMonitor:
    """Performance and population-stability monitoring primitives."""

    @staticmethod
    def population_stability_index(
        reference: list[float],
        current: list[float],
        *,
        bins: int = 10,
    ) -> float:
        if len(reference) < bins or len(current) < bins:
            raise ValueError("PSI requires at least as many observations as bins in each sample")
        reference_array = np.asarray(reference, dtype=float)
        current_array = np.asarray(current, dtype=float)
        edges = np.unique(np.quantile(reference_array, np.linspace(0, 1, bins + 1)))
        if len(edges) < 3:
            return 0.0
        edges[0], edges[-1] = -np.inf, np.inf
        expected = np.histogram(reference_array, bins=edges)[0] / len(reference_array)
        actual = np.histogram(current_array, bins=edges)[0] / len(current_array)
        expected = np.clip(expected, 1e-6, None)
        actual = np.clip(actual, 1e-6, None)
        return float(np.sum((actual - expected) * np.log(actual / expected)))

    @staticmethod
    def performance(labels: list[int], probabilities: list[float], threshold: float = 0.5) -> dict:
        return classification_metrics(
            np.asarray(labels, dtype=int),
            np.asarray(probabilities, dtype=float),
            threshold,
        )

    @staticmethod
    def drift_report(reference: dict[str, list[float]], current: dict[str, list[float]]) -> dict[str, Any]:
        features = {}
        for feature in sorted(set(reference) & set(current)):
            psi = ModelMonitor.population_stability_index(reference[feature], current[feature])
            features[feature] = {
                "psi": psi,
                "status": "critical" if psi >= 0.25 else "warning" if psi >= 0.10 else "stable",
            }
        return {
            "features": features,
            "critical_features": [name for name, item in features.items() if item["status"] == "critical"],
            "warning_features": [name for name, item in features.items() if item["status"] == "warning"],
            "limitations": "PSI detects distribution change, not performance degradation or causality.",
        }

    @staticmethod
    def check_data_quality(transactions: list[dict]) -> dict:
        if not transactions:
            return {"quality_score": 0.0, "issues": ["No transactions"], "is_usable": False}
        required = ("date", "amount", "transaction_type")
        missing = sum(value.get(field) is None for value in transactions for field in required)
        missing_rate = missing / (len(transactions) * len(required))
        duplicate_keys = [(item.get("date"), item.get("amount"), item.get("description")) for item in transactions]
        duplicate_rate = 1 - len(set(duplicate_keys)) / len(duplicate_keys)
        score = max(0.0, 1.0 - 0.6 * missing_rate - 0.4 * duplicate_rate)
        return {
            "quality_score": score,
            "missing_rate": missing_rate,
            "duplicate_rate": duplicate_rate,
            "is_usable": score >= 0.6,
        }
