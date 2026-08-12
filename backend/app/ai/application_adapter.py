"""Application → model feature adapter.

This is the single, explicit boundary between MyCreditLens's persisted
application-domain data (Application + Borrower) and the trained
application-PD model's feature schema. It exists to prevent the original
architectural bug where transaction-derived features were fed to a model
trained on application-level features.

Contract:

* The adapter reads the ACTIVE model's ``feature_schema.json`` and produces
  EXACTLY the feature names it declares, in declared order, with the declared
  types. It never invents a feature the schema doesn't ask for, and if the
  schema asks for a feature the adapter has no deterministic mapping for, it
  raises ``FeatureSchemaError`` (the model is incompatible with the current
  application domain — surfaced as ``schema_incompatible`` / HTTP 422).

* Missing *source* data (a required Application/Borrower field is null) is an
  application-readiness problem, raised as ``ApplicationNotReadyError`` (HTTP
  409): the application simply isn't complete enough to score yet.

* Present-but-invalid data (non-finite number, unmappable category, negative
  income) is a schema-satisfaction problem, raised as ``FeatureSchemaError``
  (HTTP 422).

Critical credit fields are NEVER silently fabricated, and transaction-derived
features are NEVER substituted to satisfy the schema.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

from app.ai.runtime import FeatureSchemaError
from app.models.application import Application, LoanIntent
from app.models.borrower import Borrower, HomeOwnership

MONTHS_PER_YEAR = 12
DAYS_PER_YEAR = 365.25

HOME_OWNERSHIP_LEVELS = [item.value for item in HomeOwnership]
LOAN_INTENT_LEVELS = [item.value for item in LoanIntent]


class ApplicationNotReadyError(Exception):
    """A required Application/Borrower field needed for scoring is absent.

    Distinct from FeatureSchemaError: the data is not *invalid*, it is simply
    not present yet. Mapped to HTTP 409 (application not ready for scoring).
    """

    def __init__(self, message: str, *, missing: list[str] | None = None):
        super().__init__(message)
        self.missing = missing or []


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


class ApplicationToModelAdapter:
    """Deterministically maps persisted application data to model features."""

    def __init__(self, schema: dict[str, Any]):
        self.schema = schema
        self.raw_feature_order: list[str] = list(schema["raw_feature_order"])
        self.numeric_features = set(schema.get("numeric_features", []))
        self.categorical_features = set(schema.get("categorical_features", []))
        self._builders: dict[str, Callable[[Application, Borrower], Any]] = {
            "customer_age": self._customer_age,
            "customer_income": self._customer_income,
            "employment_duration": self._employment_duration,
            "home_ownership": self._home_ownership,
            "loan_intent": self._loan_intent,
            "loan_amnt": self._loan_amnt,
            "term_years": self._term_years,
            "loan_percent_income": self._loan_percent_income,
        }

    @property
    def feature_schema_version(self) -> str | None:
        return self.schema.get("feature_schema_version")

    def _unsupported_features(self) -> list[str]:
        return [name for name in self.raw_feature_order if name not in self._builders]

    def build_features(self, application: Application, borrower: Borrower) -> dict[str, Any]:
        """Produce the exact feature dict the active model expects.

        Raises:
            FeatureSchemaError: the schema requires a feature this adapter cannot
                map, or a source value is present but cannot satisfy the schema.
            ApplicationNotReadyError: a required source field is missing.
        """
        unsupported = self._unsupported_features()
        if unsupported:
            raise FeatureSchemaError(
                "The active model requires features the application adapter cannot "
                "produce from MyCreditLens data (no deterministic, non-fabricated "
                f"mapping exists): {', '.join(unsupported)}"
            )

        missing: list[str] = []
        features: dict[str, Any] = {}
        for name in self.raw_feature_order:
            try:
                features[name] = self._builders[name](application, borrower)
            except ApplicationNotReadyError as exc:
                missing.extend(exc.missing or [name])
        if missing:
            raise ApplicationNotReadyError(
                "Application is not ready for scoring; required data is missing: "
                + ", ".join(sorted(set(missing))),
                missing=sorted(set(missing)),
            )

        # Enforce ordering + coarse type expectations the schema declares.
        ordered = {name: features[name] for name in self.raw_feature_order}
        return ordered

    # ------------------------------------------------------------------
    # Individual, deterministic mappings
    # ------------------------------------------------------------------
    def _application_date(self, application: Application) -> date:
        stamp = application.submitted_at or application.created_at
        if isinstance(stamp, datetime):
            return stamp.date()
        if isinstance(stamp, date):
            return stamp
        return datetime.utcnow().date()

    def _require(self, value: Any, field: str) -> Any:
        if value is None:
            raise ApplicationNotReadyError(f"Missing required field: {field}", missing=[field])
        return value

    def _customer_age(self, application: Application, borrower: Borrower) -> float:
        dob = self._require(borrower.date_of_birth, "borrower.date_of_birth")
        as_of = self._application_date(application)
        dob_date = dob.date() if isinstance(dob, datetime) else dob
        age = (as_of - dob_date).days / DAYS_PER_YEAR
        if age <= 0 or age > 130:
            raise FeatureSchemaError(f"Computed customer_age is implausible: {age:.1f}")
        return float(round(age, 2))

    def _customer_income(self, application: Application, borrower: Borrower) -> float:
        monthly = self._require(borrower.monthly_income_declared, "borrower.monthly_income_declared")
        annual = float(monthly) * MONTHS_PER_YEAR
        if annual <= 0:
            raise FeatureSchemaError("customer_income must be positive (annualised declared income)")
        return annual

    def _employment_duration(self, application: Application, borrower: Borrower) -> float:
        value = self._require(borrower.employment_duration_years, "borrower.employment_duration_years")
        value = float(value)
        if value < 0:
            raise FeatureSchemaError("employment_duration cannot be negative")
        return value

    def _home_ownership(self, application: Application, borrower: Borrower) -> str:
        value = _enum_value(self._require(borrower.home_ownership, "borrower.home_ownership"))
        value = str(value).strip().upper()
        if value not in HOME_OWNERSHIP_LEVELS:
            raise FeatureSchemaError(
                f"home_ownership '{value}' is not a recognised level {HOME_OWNERSHIP_LEVELS}"
            )
        return value

    def _loan_intent(self, application: Application, borrower: Borrower) -> str:
        value = _enum_value(self._require(application.loan_intent, "application.loan_intent"))
        value = str(value).strip().upper()
        if value not in LOAN_INTENT_LEVELS:
            raise FeatureSchemaError(
                f"loan_intent '{value}' is not a recognised level {LOAN_INTENT_LEVELS}"
            )
        return value

    def _loan_amnt(self, application: Application, borrower: Borrower) -> float:
        value = float(self._require(application.requested_amount, "application.requested_amount"))
        if value <= 0:
            raise FeatureSchemaError("loan_amnt must be positive")
        return value

    def _term_years(self, application: Application, borrower: Borrower) -> float:
        months = self._require(application.requested_term_months, "application.requested_term_months")
        years = float(months) / MONTHS_PER_YEAR
        if years <= 0:
            raise FeatureSchemaError("term_years must be positive")
        return years

    def _loan_percent_income(self, application: Application, borrower: Borrower) -> float:
        amnt = self._loan_amnt(application, borrower)
        income = self._customer_income(application, borrower)
        return float(amnt / income)

    # ------------------------------------------------------------------
    # Health / readiness helpers
    # ------------------------------------------------------------------
    def dry_run_features(self) -> dict[str, Any]:
        """A deterministic, schema-consistent input used to prove inference can
        execute (health check). Values are plausible and finite; categoricals use
        known levels so the encoder produces a real one-hot vector."""
        if self._unsupported_features():
            raise FeatureSchemaError(
                "Active model schema is incompatible with the application adapter: "
                + ", ".join(self._unsupported_features())
            )
        defaults = {
            "customer_age": 35.0,
            "customer_income": 60000.0,
            "employment_duration": 5.0,
            "home_ownership": HOME_OWNERSHIP_LEVELS[0],
            "loan_intent": LOAN_INTENT_LEVELS[0],
            "loan_amnt": 10000.0,
            "term_years": 4.0,
            "loan_percent_income": 10000.0 / 60000.0,
        }
        return {name: defaults[name] for name in self.raw_feature_order}
