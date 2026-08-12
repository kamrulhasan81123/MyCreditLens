from __future__ import annotations

from copy import deepcopy

from app.ai.runtime import CreditModelRuntime


class CounterfactualGenerator:
    """Constrained model what-if analysis over the application-PD feature
    contract. Results are model-sensitivity analysis, not causal promises.

    Operates ONLY on inference-safe application features and re-scores through
    the same runtime as production scoring. Derived features (loan_percent_income)
    are recomputed after each perturbation so scenarios stay internally
    consistent.
    """

    # feature -> (multipliers, feasibility note, direction of change)
    ACTIONS = {
        "customer_income": ((1.10, 1.25, 1.50), "Increase verified income", "increase"),
        "loan_amnt": ((0.90, 0.75, 0.50), "Request a smaller loan amount", "decrease"),
        "employment_duration": ((1.25, 1.50, 2.0), "Longer employment tenure", "increase"),
        "term_years": ((1.25, 1.50), "Extend the loan term", "increase"),
    }

    @staticmethod
    def _recompute_derived(features: dict[str, float]) -> None:
        if "loan_percent_income" in features and features.get("customer_income"):
            features["loan_percent_income"] = float(features["loan_amnt"]) / float(features["customer_income"])

    @classmethod
    def generate(
        cls,
        runtime: CreditModelRuntime,
        features: dict[str, float],
        *,
        target_probability: float | None = None,
        limit: int = 5,
    ) -> dict:
        baseline = runtime.predict(features, include_explanation=False)
        target = target_probability if target_probability is not None else runtime.thresholds.medium_max
        trained_features = set(runtime.schema["raw_feature_order"])
        scenarios = []
        for feature, (multipliers, feasibility, direction) in cls.ACTIONS.items():
            if feature not in features or feature not in trained_features:
                continue
            current = float(features[feature])
            best = None
            for multiplier in multipliers:
                candidate = deepcopy(features)
                candidate[feature] = current * multiplier
                cls._recompute_derived(candidate)
                prediction = runtime.predict(candidate, include_explanation=False)
                reduction = baseline.probability_of_default - prediction.probability_of_default
                if reduction > 0 and (best is None or reduction > best["probability_reduction"]):
                    best = {
                        "feature": feature,
                        "changed_features": {feature: {"from": current, "to": candidate[feature]}},
                        "original_probability": baseline.probability_of_default,
                        "simulated_probability": prediction.probability_of_default,
                        "probability_reduction": reduction,
                        "original_risk_band": baseline.risk_band,
                        "simulated_risk_band": prediction.risk_band,
                        "feasibility": feasibility,
                        "target_reached": prediction.probability_of_default <= target,
                        # Aliases consumed by the existing frontend simulator.
                        "current_value": current,
                        "suggested_value": candidate[feature],
                        "current_probability": baseline.probability_of_default,
                        "projected_probability": prediction.probability_of_default,
                    }
            if best:
                scenarios.append(best)
        scenarios.sort(key=lambda item: item["probability_reduction"], reverse=True)
        return {
            "model_version": runtime.model_version,
            "feature_schema_version": runtime.feature_schema_version,
            "original_probability": baseline.probability_of_default,
            "original_risk_band": baseline.risk_band,
            "target_probability": target,
            "scenarios": scenarios[:limit],
            "warning": (
                "Model sensitivity analysis only. These changes do not guarantee approval "
                "and do not establish a causal effect on real-world default risk."
            ),
            # `disclaimer` kept for the existing frontend simulator.
            "disclaimer": (
                "Model sensitivity analysis only. These changes do not guarantee approval "
                "and do not establish a causal effect on real-world default risk."
            ),
        }
