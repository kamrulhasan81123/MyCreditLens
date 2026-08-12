from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.application_adapter import ApplicationNotReadyError, ApplicationToModelAdapter
from app.ai.feature_engineer import FeatureEngineer
from app.ai.runtime import (
    ArtifactUnavailableError,
    CreditModelRuntime,
    FeatureSchemaError,
    InferenceResult,
    load_credit_runtime,
)
from app.config import settings
from app.models.application import Application
from app.models.borrower import Borrower
from app.models.consent import Consent
from app.models.data_source import DataSource
from app.models.explanation import Explanation
from app.models.feature import EngineeredFeature
from app.models.model import MLModel
from app.models.prediction import Prediction
from app.models.transaction import Transaction
from app.services.audit_service import add_audit_log

# Consent that must be granted before an application may be scored (§9).
SCORING_CONSENT_TYPE = "credit_scoring"


class ScoringService:
    """Artifact-backed application-PD scoring.

    The canonical scoring path is:
        Application + Borrower -> ApplicationToModelAdapter -> preprocessor ->
        model -> calibrator -> probability -> risk band -> OOD/uncertainty ->
        SHAP explanation -> persisted Prediction.

    Transaction / bank-statement features are computed and persisted separately
    (alternative-data lineage) and are NEVER fed into the application-PD model.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Canonical scoring
    # ------------------------------------------------------------------
    async def score_application(self, application_id: str, model_version: str | None = None) -> Prediction:
        application, borrower = await self._get_scorable_application(application_id)
        await self._ensure_scoring_consent(application_id)

        runtime = self._load_runtime_or_none()
        if runtime is not None:
            if model_version and runtime.model_version != model_version:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Requested model version is not the deployed artifact version",
                )
            features = self._build_features(runtime, application, borrower)
            try:
                result = runtime.predict(features)
            except FeatureSchemaError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            except ArtifactUnavailableError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
            scoring_mode = "trained_artifact"
            model = await self._model_record(
                name=result.model_name,
                version=result.model_version,
                model_type=runtime.metadata.get("algorithm", runtime.metadata.get("selected_model", "unknown")),
                metrics=runtime.metadata.get("test_metrics", {}),
                parameters={
                    "calibration_method": runtime.metadata.get("calibration_method"),
                    "artifact_contract_version": runtime.metadata.get("artifact_contract_version"),
                    "feature_schema_version": result.feature_schema_version,
                },
                feature_names=list(runtime.schema["raw_feature_order"]),
            )
        else:
            if settings.require_model_artifacts or not settings.allow_demo_scoring:
                raise HTTPException(
                    status_code=503, detail="A verified trained model artifact bundle is required"
                )
            result = self._demo_result(application, borrower)
            scoring_mode = "demo_rules"
            model = await self._model_record(
                name="DemoCreditRiskRules",
                version="demo-1.0.0",
                model_type="demo_rules",
                metrics={},
                parameters={"warning": "Workflow-only deterministic fallback; not trained AI."},
                feature_names=list(result.feature_values),
            )

        # Preserve transaction/alt-data lineage separately (never fed to the PD model).
        await self._persist_transaction_features(application)

        prediction = Prediction(
            application_id=application.id,
            model_id=model.id,
            probability_of_default=result.probability_of_default,
            raw_probability=result.raw_probability,
            calibrated_probability=result.calibrated_probability,
            risk_band=result.risk_band,
            confidence=result.confidence,
            uncertainty=result.uncertainty,
            is_ood=result.is_ood,
            ood_score=result.ood_score,
            calibration_status="calibrated" if scoring_mode == "trained_artifact" else "demo_untrained",
            scoring_mode=scoring_mode,
            model_version=result.model_version,
            feature_schema_version=result.feature_schema_version,
            feature_values={"scoring_mode": scoring_mode, **result.feature_values},
        )
        self.db.add(prediction)
        await self.db.flush()
        self.db.add(self._explanation(prediction, result, scoring_mode))

        application.status = "scored"
        application.risk_band = result.risk_band
        application.scored_at = datetime.utcnow()
        application.probability_of_default = result.probability_of_default
        application.confidence = result.confidence
        application.model_version = result.model_version
        application.recommended_action = self._recommended_action(result)
        add_audit_log(
            self.db,
            user_id=None,
            action="application.scored",
            resource_type="prediction",
            resource_id=prediction.id,
            details={
                "application_id": application.id,
                "model_version": result.model_version,
                "feature_schema_version": result.feature_schema_version,
                "mode": scoring_mode,
            },
        )
        await self.db.commit()
        await self.db.refresh(prediction)
        return prediction

    # ------------------------------------------------------------------
    # Shared feature-builder path (used by scoring, counterfactual, stress)
    # ------------------------------------------------------------------
    def _build_features(self, runtime: CreditModelRuntime, application: Application, borrower: Borrower) -> dict[str, Any]:
        adapter = ApplicationToModelAdapter(runtime.schema)
        try:
            return adapter.build_features(application, borrower)
        except ApplicationNotReadyError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except FeatureSchemaError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    async def prepare_scoring_inputs(
        self, application_id: str, *, model_version: str | None = None
    ) -> tuple[Application, Borrower, CreditModelRuntime, dict[str, Any]]:
        """Load runtime + build model features through the SAME adapter path as
        production scoring. Used by counterfactual and stress-test endpoints so
        they never build a second, incompatible feature representation."""
        application, borrower = await self._get_scorable_application(application_id)
        runtime = self._require_runtime()
        if model_version and runtime.model_version != model_version:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Requested model version is not deployed")
        features = self._build_features(runtime, application, borrower)
        return application, borrower, runtime, features

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    async def get_latest_prediction(self, application_id: str) -> Prediction:
        result = await self.db.execute(
            select(Prediction).where(Prediction.application_id == application_id).order_by(Prediction.scored_at.desc())
        )
        prediction = result.scalars().first()
        if not prediction:
            raise HTTPException(status_code=404, detail="No prediction found")
        return prediction

    async def has_explanation(self, prediction_id: str) -> bool:
        result = await self.db.execute(
            select(Explanation.id).where(Explanation.prediction_id == prediction_id)
        )
        return result.first() is not None

    async def get_latest_explanation(self, application_id: str) -> Explanation:
        result = await self.db.execute(
            select(Explanation)
            .where(Explanation.application_id == application_id)
            .order_by(Explanation.generated_at.desc())
        )
        explanation = result.scalars().first()
        if not explanation:
            raise HTTPException(status_code=404, detail="No explanation found. Run scoring first.")
        return explanation

    # ------------------------------------------------------------------
    # Runtime loading
    # ------------------------------------------------------------------
    def _load_runtime_or_none(self) -> CreditModelRuntime | None:
        artifact_dir = settings.resolved_model_artifact_path
        if not (artifact_dir / "manifest.json").is_file():
            if settings.require_model_artifacts or not settings.allow_demo_scoring:
                raise HTTPException(status_code=503, detail="A verified trained model artifact bundle is required")
            return None
        try:
            return load_credit_runtime(artifact_dir)
        except ArtifactUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    def _require_runtime(self) -> CreditModelRuntime:
        runtime = self._load_runtime_or_none()
        if runtime is None:
            raise HTTPException(status_code=503, detail="A verified trained model artifact bundle is required")
        return runtime

    # ------------------------------------------------------------------
    # Application / consent readiness
    # ------------------------------------------------------------------
    async def _get_scorable_application(self, application_id: str) -> tuple[Application, Borrower]:
        result = await self.db.execute(select(Application).where(Application.id == application_id))
        application = result.scalar_one_or_none()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        status_value = application.status.value if hasattr(application.status, "value") else application.status
        if status_value not in ("submitted", "scored"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application must be submitted before scoring",
            )
        borrower = (
            await self.db.execute(select(Borrower).where(Borrower.id == application.borrower_id))
        ).scalar_one_or_none()
        if not borrower:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application is not ready for scoring; borrower profile is missing",
            )
        return application, borrower

    async def _ensure_scoring_consent(self, application_id: str) -> None:
        result = await self.db.execute(
            select(Consent).where(
                Consent.application_id == application_id,
                Consent.data_source_type == SCORING_CONSENT_TYPE,
                Consent.granted.is_(True),
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Credit-scoring consent has not been granted for this application",
            )

    # ------------------------------------------------------------------
    # Transaction / alternative-data lineage (preserved, separate from PD model)
    # ------------------------------------------------------------------
    async def transaction_features_for_application(self, application: Application) -> dict[str, float]:
        result = await self.db.execute(
            select(Transaction)
            .join(DataSource, Transaction.data_source_id == DataSource.id)
            .where(DataSource.application_id == application.id, Transaction.is_excluded.is_(False))
        )
        transactions = [
            {
                "date": transaction.transaction_date,
                "amount": transaction.amount,
                "transaction_type": transaction.direction,
                "description": transaction.description,
                "category": transaction.analyst_category or transaction.category,
                "balance_after": None,
            }
            for transaction in result.scalars().all()
        ]
        if not transactions:
            return {}
        features = FeatureEngineer.engineer_features(transactions)
        features["requested_amount"] = float(application.requested_amount)
        features["requested_term_months"] = float(application.requested_term_months or 0)
        return features

    async def _persist_transaction_features(self, application: Application) -> None:
        """Compute and persist transaction-derived features as separate
        alternative-data lineage. Best-effort: absence of transactions must not
        block application-PD scoring."""
        features = await self.transaction_features_for_application(application)
        for name, value in features.items():
            self.db.add(
                EngineeredFeature(
                    application_id=application.id,
                    feature_name=name,
                    feature_value=float(value),
                    feature_version="transaction_features_v1",
                    data_lineage="Derived from non-excluded transactions; alternative-data signal, not a PD model input.",
                )
            )

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    async def _model_record(
        self,
        *,
        name: str,
        version: str,
        model_type: str,
        metrics: dict,
        parameters: dict,
        feature_names: list[str],
    ) -> MLModel:
        result = await self.db.execute(select(MLModel).where(MLModel.version == version, MLModel.model_name == name))
        model = result.scalar_one_or_none()
        if model:
            return model
        model = MLModel(
            model_name=name,
            version=version,
            model_type=model_type,
            is_active=True,
            model_path=str(settings.resolved_model_artifact_path),
            metrics=metrics,
            parameters=parameters,
            feature_names=feature_names,
            trained_at=datetime.utcnow() if model_type != "demo_rules" else None,
        )
        self.db.add(model)
        await self.db.flush()
        return model

    def _demo_result(self, application: Application, borrower: Borrower) -> InferenceResult:
        """Deterministic non-AI fallback used only when no artifact is available
        and demo scoring is explicitly enabled. Uses application-level inputs
        (never transaction features) so it stays coherent with the PD contract."""
        income = float(borrower.monthly_income_declared or 0) * 12
        amnt = float(application.requested_amount or 0)
        lpi = amnt / income if income > 0 else 1.0
        raw = -1.2 + 2.5 * min(lpi, 2.0)
        probability = float(np.clip(1 / (1 + np.exp(-raw)), 0.01, 0.99))
        band = "low" if probability < 0.15 else "medium" if probability < 0.30 else "high"
        contributions = [
            {
                "feature": "loan_percent_income",
                "label": "Loan Percent Income",
                "value": lpi,
                "contribution": lpi,
                "direction": "increases_risk",
            }
        ]
        return InferenceResult(
            probability_of_default=probability,
            risk_band=band,
            confidence=0.3,
            is_ood=False,
            ood_score=0.0,
            model_version="demo-1.0.0",
            model_name="DemoCreditRiskRules",
            feature_values={"loan_percent_income": lpi, "customer_income": income, "loan_amnt": amnt},
            contributions=contributions,
            plain_language_explanation=(
                "Demo scoring mode is active. This deterministic workflow result is not a trained or calibrated AI prediction."
            ),
            raw_probability=probability,
            calibrated_probability=probability,
            uncertainty=0.7,
            feature_schema_version=None,
        )

    def _explanation(self, prediction: Prediction, result: InferenceResult, mode: str) -> Explanation:
        positive = [item for item in result.contributions if item["contribution"] > 0][:5]
        negative = [item for item in result.contributions if item["contribution"] < 0][:5]
        return Explanation(
            application_id=prediction.application_id,
            prediction_id=prediction.id,
            method="shap" if mode == "trained_artifact" else "demo_feature_contribution",
            shap_values={item["feature"]: item["contribution"] for item in result.contributions},
            top_positive_factors={item["feature"]: item["contribution"] for item in positive},
            top_negative_factors={item["feature"]: item["contribution"] for item in negative},
            plain_language_explanation=result.plain_language_explanation,
        )

    def _recommended_action(self, result: InferenceResult) -> str:
        if result.is_ood or result.confidence < 0.45:
            return "manual_review"
        if result.risk_band == "low":
            return "approve"
        if result.risk_band == "medium":
            return "manual_review"
        return "reject"
