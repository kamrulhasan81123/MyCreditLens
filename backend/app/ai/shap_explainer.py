from __future__ import annotations

import re
from typing import Any


class ShapExplainer:
    """Controlled presentation helpers for real model contributions."""

    REASON_TEMPLATES = {
        # Application-PD model features (active model).
        "customer_age": "Applicant age affected the assessment.",
        "customer_income": "Declared income affected the assessment.",
        "employment_duration": "Length of employment affected the assessment.",
        "home_ownership": "Home-ownership status affected the assessment.",
        "loan_intent": "The stated loan purpose affected the assessment.",
        "loan_amnt": "The requested loan amount affected the assessment.",
        "term_years": "The requested loan term affected the assessment.",
        "loan_percent_income": "The loan-to-income ratio affected the assessment.",
        # Transaction / alternative-data features (separate layer).
        "income_stability_score": "Income regularity affected the assessment.",
        "monthly_income_mean": "Average income affected the assessment.",
        "monthly_income_std": "Income variability affected the assessment.",
        "monthly_expense_mean": "Average expenses affected the assessment.",
        "avg_balance": "Average account balance affected the assessment.",
        "min_balance": "The minimum observed balance affected the assessment.",
        "net_monthly_cashflow": "Net monthly cash flow affected the assessment.",
        "cashflow_volatility": "Cash-flow variability affected the assessment.",
        "overdraft_count": "Observed overdraft incidents affected the assessment.",
        "dti_ratio": "The expense-to-income ratio affected the assessment.",
        "savings_rate": "The observed savings rate affected the assessment.",
        "buffer_months": "The estimated liquidity buffer affected the assessment.",
        "days_of_data": "The available transaction-history length affected confidence.",
        "transaction_count": "The amount of available transaction evidence affected confidence.",
    }

    @classmethod
    def raw_feature_name(cls, transformed_name: str) -> str:
        name = transformed_name.split("__", 1)[-1]
        for feature in sorted(cls.REASON_TEMPLATES, key=len, reverse=True):
            if name == feature or name.startswith(feature + "_"):
                return feature
        return name

    @classmethod
    def label(cls, transformed_name: str) -> str:
        raw = cls.raw_feature_name(transformed_name)
        return re.sub(r"\s+", " ", raw.replace("_", " ")).strip().title()

    @classmethod
    def controlled_summary(cls, contributions: list[dict[str, Any]], probability: float) -> str:
        reasons = []
        for item in contributions[:5]:
            raw = cls.raw_feature_name(item["feature"])
            template = cls.REASON_TEMPLATES.get(raw, f"{cls.label(raw)} affected the assessment.")
            direction = "increased" if item["direction"] == "increases_risk" else "reduced"
            reasons.append(f"{template[:-1]} and {direction} assessed risk.")
        prefix = f"The calibrated probability of default is {probability:.1%}."
        return " ".join([prefix, *reasons])
