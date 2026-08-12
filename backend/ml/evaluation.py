from __future__ import annotations

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def expected_calibration_error(labels: np.ndarray, probabilities: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    score = 0.0
    for lower, upper in zip(edges[:-1], edges[1:]):
        mask = (probabilities >= lower) & (probabilities < upper if upper < 1 else probabilities <= upper)
        if not np.any(mask):
            continue
        score += float(mask.mean()) * abs(float(labels[mask].mean()) - float(probabilities[mask].mean()))
    return float(score)


def ks_statistic(labels: np.ndarray, probabilities: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(labels, probabilities)
    return float(np.max(tpr - fpr))


def classification_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
) -> dict:
    if len(np.unique(labels)) != 2:
        raise ValueError("Evaluation labels must contain both classes")
    predictions = (probabilities >= threshold).astype(int)
    matrix = confusion_matrix(labels, predictions, labels=[0, 1])
    fraction, mean = calibration_curve(labels, probabilities, n_bins=10, strategy="quantile")
    return {
        "roc_auc": float(roc_auc_score(labels, probabilities)),
        "pr_auc": float(average_precision_score(labels, probabilities)),
        "brier_score": float(brier_score_loss(labels, probabilities)),
        "log_loss": float(log_loss(labels, probabilities, labels=[0, 1])),
        "precision_default": float(precision_score(labels, predictions, zero_division=0)),
        "recall_default": float(recall_score(labels, predictions, zero_division=0)),
        "f1_default": float(f1_score(labels, predictions, zero_division=0)),
        "expected_calibration_error": expected_calibration_error(labels, probabilities),
        "ks_statistic": ks_statistic(labels, probabilities),
        "threshold": threshold,
        "confusion_matrix": matrix.tolist(),
        "calibration_curve": {
            "mean_predicted_probability": mean.tolist(),
            "observed_default_rate": fraction.tolist(),
        },
    }
