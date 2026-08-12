from __future__ import annotations

from copy import deepcopy

from app.ai.runtime import CreditModelRuntime


class StressTester:
    """Scores explicit adverse shocks through the deployed application-PD model.

    Shocks modify only the model's own inference-safe input features and
    re-score through the same runtime. Derived features (loan_percent_income)
    are recomputed so scenarios stay consistent.

    Note: expense/remittance/business-sales stresses belong to the separate
    transaction / alternative-data layer (they are not inputs to this
    application-PD model). Here we stress the income and requested-loan inputs
    that the model actually consumes.
    """

    # scenario -> {feature: multiplier}
    SCENARIOS = {
        "income_decrease_20pct": {"customer_income": 0.80},
        "income_decrease_50pct": {"customer_income": 0.50},
        "requested_loan_increase_25pct": {"loan_amnt": 1.25},
        "requested_loan_increase_50pct": {"loan_amnt": 1.50},
        "combined_income_drop_and_larger_loan": {"customer_income": 0.80, "loan_amnt": 1.25},
    }

    @staticmethod
    def _recompute_derived(features: dict[str, float]) -> None:
        if "loan_percent_income" in features and features.get("customer_income"):
            features["loan_percent_income"] = float(features["loan_amnt"]) / float(features["customer_income"])

    @classmethod
    def run(cls, runtime: CreditModelRuntime, features: dict[str, float]) -> dict:
        baseline = runtime.predict(features, include_explanation=False)
        trained_features = set(runtime.schema["raw_feature_order"])
        results = []
        for name, shocks in cls.SCENARIOS.items():
            candidate = deepcopy(features)
            applied = {}
            for feature, multiplier in shocks.items():
                if feature in candidate and feature in trained_features:
                    candidate[feature] = float(candidate[feature]) * multiplier
                    applied[feature] = multiplier
            if not applied:
                continue
            cls._recompute_derived(candidate)
            prediction = runtime.predict(candidate, include_explanation=False)
            results.append(
                {
                    "scenario": name,
                    "applied_multipliers": applied,
                    "probability_of_default": prediction.probability_of_default,
                    "probability_change": prediction.probability_of_default - baseline.probability_of_default,
                    "risk_band": prediction.risk_band,
                    "is_ood": prediction.is_ood,
                }
            )
        return {
            "model_version": runtime.model_version,
            "feature_schema_version": runtime.feature_schema_version,
            "baseline_probability": baseline.probability_of_default,
            "baseline_risk_band": baseline.risk_band,
            "scenarios": results,
            "worst_case_probability": max(
                [item["probability_of_default"] for item in results],
                default=baseline.probability_of_default,
            ),
            "warning": "Scenario analysis depends on specified feature shocks and is not a macroeconomic forecast.",
            # `disclaimer` kept for the existing frontend stress panel.
            "disclaimer": "Scenario analysis depends on specified feature shocks and is not a macroeconomic forecast.",
        }
