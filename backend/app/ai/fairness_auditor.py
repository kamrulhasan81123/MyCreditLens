from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
from sklearn.metrics import confusion_matrix


class FairnessAuditor:
    """Group outcome/error analysis with explicit sample-size limitations."""

    @staticmethod
    def evaluate(
        labels: list[int],
        probabilities: list[float],
        groups: list[str],
        *,
        threshold: float = 0.50,
        minimum_group_size: int = 30,
    ) -> dict[str, Any]:
        if not (len(labels) == len(probabilities) == len(groups)) or not labels:
            raise ValueError("Labels, probabilities, and groups must be non-empty and have equal length")
        y = np.asarray(labels, dtype=int)
        probability = np.asarray(probabilities, dtype=float)
        if set(np.unique(y)) != {0, 1}:
            raise ValueError("Fairness evaluation requires both binary outcome classes")
        if np.any((probability < 0) | (probability > 1)):
            raise ValueError("Probabilities must be between zero and one")
        predictions = (probability >= threshold).astype(int)
        group_metrics = {}
        excluded = {}
        for group, count in Counter(groups).items():
            mask = np.asarray([value == group for value in groups])
            if count < minimum_group_size:
                excluded[group] = {"count": count, "reason": "insufficient_sample"}
                continue
            tn, fp, fn, tp = confusion_matrix(y[mask], predictions[mask], labels=[0, 1]).ravel()
            group_metrics[group] = {
                "count": count,
                "observed_default_rate": float(y[mask].mean()),
                "mean_predicted_default": float(probability[mask].mean()),
                "approval_rate_at_threshold": float((predictions[mask] == 0).mean()),
                "true_positive_rate": float(tp / (tp + fn)) if tp + fn else None,
                "false_positive_rate": float(fp / (fp + tn)) if fp + tn else None,
                "positive_predictive_value": float(tp / (tp + fp)) if tp + fp else None,
            }
        if len(group_metrics) < 2:
            return {
                "status": "insufficient_groups",
                "group_metrics": group_metrics,
                "excluded_groups": excluded,
                "limitations": ["At least two groups meeting the minimum sample size are required."],
            }
        approval_rates = [item["approval_rate_at_threshold"] for item in group_metrics.values()]
        tprs = [item["true_positive_rate"] for item in group_metrics.values() if item["true_positive_rate"] is not None]
        fprs = [item["false_positive_rate"] for item in group_metrics.values() if item["false_positive_rate"] is not None]
        max_approval = max(approval_rates)
        return {
            "status": "evaluated",
            "threshold": threshold,
            "minimum_group_size": minimum_group_size,
            "group_metrics": group_metrics,
            "excluded_groups": excluded,
            "disparities": {
                "demographic_parity_difference": max(approval_rates) - min(approval_rates),
                "disparate_impact_ratio": min(approval_rates) / max_approval if max_approval else None,
                "equal_opportunity_difference": max(tprs) - min(tprs) if len(tprs) >= 2 else None,
                "false_positive_rate_difference": max(fprs) - min(fprs) if len(fprs) >= 2 else None,
            },
            "review_flags": {
                "four_fifths_below_0_8": bool(max_approval and min(approval_rates) / max_approval < 0.8),
                "equal_opportunity_difference_above_0_1": bool(len(tprs) >= 2 and max(tprs) - min(tprs) > 0.1),
            },
            "limitations": [
                "Flags are screening heuristics, not a legal fairness determination.",
                "Results depend on label quality, threshold choice, group definitions, and sample size.",
            ],
        }

    @staticmethod
    def calculate_fairness_metrics(scores, labels, groups) -> dict:
        probabilities = [float(score) if float(score) <= 1 else 1 - (float(score) - 300) / 550 for score in scores]
        probabilities = [min(1.0, max(0.0, value)) for value in probabilities]
        return FairnessAuditor.evaluate(labels, probabilities, groups)
