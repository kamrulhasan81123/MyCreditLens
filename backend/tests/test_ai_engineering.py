from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

import ml.training as training
from app.ai.fairness_auditor import FairnessAuditor
from app.ai.model_monitor import ModelMonitor
from app.ai.runtime import CreditModelRuntime
from ml.contracts import RiskThresholds, verify_manifest
from ml.training import TrainingConfig, train_credit_model


def labelled_fixture(rows: int = 320) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    income = rng.lognormal(mean=8.4, sigma=0.35, size=rows)
    expenses = income * rng.uniform(0.35, 1.15, size=rows)
    savings_rate = (income - expenses) / income
    dti_ratio = expenses / income
    stability = rng.beta(5, 2, size=rows)
    logit = -2.0 + 2.8 * dti_ratio - 1.4 * savings_rate - 1.0 * stability
    probability = 1 / (1 + np.exp(-logit))
    target = rng.binomial(1, probability)
    return pd.DataFrame(
        {
            "monthly_income_mean": income,
            "monthly_expense_mean": expenses,
            "savings_rate": savings_rate,
            "dti_ratio": dti_ratio,
            "income_stability_score": stability,
            "default_90d": target,
        }
    )


def test_training_exports_verified_runtime_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr(
        training,
        "_candidate_models",
        lambda random_state: {
            "logistic_regression": LogisticRegression(
                class_weight="balanced", max_iter=1000, random_state=random_state
            )
        },
    )
    frame = labelled_fixture()
    metadata = train_credit_model(
        frame,
        TrainingConfig(
            target_column="default_90d",
            output_dir=tmp_path,
            model_version="test-1.0.0",
            dataset_name="synthetic_test_fixture",
            target_definition="Synthetic binary fixture used only for pipeline testing",
            thresholds=RiskThresholds(),
        ),
    )
    assert metadata["selected_model"] == "logistic_regression"
    assert 0 <= metadata["test_metrics"]["brier_score"] <= 1
    verify_manifest(tmp_path)

    runtime = CreditModelRuntime(tmp_path)
    row = frame.drop(columns=["default_90d"]).iloc[0].to_dict()
    prediction = runtime.predict(row)
    assert 0 <= prediction.probability_of_default <= 1
    assert prediction.risk_band in {"low", "medium", "high"}
    assert prediction.contributions
    assert "calibrated probability" in prediction.plain_language_explanation.lower()


def test_leakage_columns_are_rejected(tmp_path):
    frame = labelled_fixture().rename(columns={"income_stability_score": "future_collection_status"})
    with pytest.raises(ValueError, match="leakage"):
        train_credit_model(
            frame,
            TrainingConfig(
                target_column="default_90d",
                output_dir=tmp_path,
                target_definition="test",
            ),
        )


def test_fairness_requires_adequate_groups():
    labels = [0, 1] * 40
    probabilities = [0.2, 0.8] * 40
    groups = ["a"] * 40 + ["b"] * 40
    report = FairnessAuditor.evaluate(labels, probabilities, groups, minimum_group_size=30)
    assert report["status"] == "evaluated"
    assert "disparate_impact_ratio" in report["disparities"]
    assert report["limitations"]


def test_population_stability_index_detects_shift():
    reference = np.linspace(0, 1, 200).tolist()
    stable = (np.linspace(0, 1, 200) + 0.001).tolist()
    shifted = np.linspace(1, 2, 200).tolist()
    assert ModelMonitor.population_stability_index(reference, stable) < 0.1
    assert ModelMonitor.population_stability_index(reference, shifted) > 0.25
