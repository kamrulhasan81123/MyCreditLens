"""Decision Room aggregation — real, persisted/computed values only.

Assembles everything the Decision Room needs from the database and the
transaction pipeline. Where a value cannot be computed it returns the string
``"not_available"`` or a ``{"status": "insufficient_data"}`` block — it never
fabricates a number.

Credit risk, fraud/integrity risk, data reliability, and cash-flow analytics are
kept as SEPARATE concepts. Cash-flow / reliability do not alter the PD.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.feature_engineer import FeatureEngineer
from app.models.application import Application
from app.models.audit_log import AuditLog
from app.models.borrower import Borrower
from app.models.consent import Consent
from app.models.data_source import DataSource
from app.models.decision import Decision
from app.models.explanation import Explanation
from app.models.integrity_alert import IntegrityAlert
from app.models.prediction import Prediction
from app.models.transaction import Transaction

NOT_AVAILABLE = "not_available"
INSUFFICIENT = {"status": "insufficient_data"}


def _enum(v: Any) -> Any:
    return v.value if hasattr(v, "value") else v


class DecisionRoomService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build(self, application: Application) -> dict[str, Any]:
        borrower = (
            await self.db.execute(select(Borrower).where(Borrower.id == application.borrower_id))
        ).scalar_one_or_none()
        prediction = (
            await self.db.execute(
                select(Prediction).where(Prediction.application_id == application.id).order_by(Prediction.scored_at.desc())
            )
        ).scalars().first()
        explanation = (
            await self.db.execute(
                select(Explanation).where(Explanation.application_id == application.id).order_by(Explanation.generated_at.desc())
            )
        ).scalars().first()

        return {
            "application": self._application_block(application, borrower),
            "scoring": self._scoring_block(prediction),
            "explanation": self._explanation_block(explanation),
            "data_reliability": await self._data_reliability(application.id),
            "cash_flow": await self._cash_flow(application),
            "integrity_alerts": await self._integrity_alerts(application, borrower),
            "model_agreement": self._model_agreement(prediction),
            "timeline": await self._timeline(application),
        }

    # ------------------------------------------------------------------
    def _application_block(self, app: Application, borrower: Borrower | None) -> dict[str, Any]:
        return {
            "id": app.id,
            "reference": app.reference,
            "borrower_id": app.borrower_id,
            "borrower_type": _enum(borrower.borrower_type) if borrower else NOT_AVAILABLE,
            "requested_amount": app.requested_amount,
            "requested_term_months": app.requested_term_months,
            "purpose": app.purpose,
            "loan_intent": _enum(app.loan_intent) or NOT_AVAILABLE,
            "status": _enum(app.status),
            "recommended_action": app.recommended_action or NOT_AVAILABLE,
        }

    def _scoring_block(self, p: Prediction | None) -> dict[str, Any]:
        if not p:
            return {"status": "not_scored"}
        return {
            "probability_of_default": p.probability_of_default,
            "calibrated_probability": p.calibrated_probability,
            "raw_probability": p.raw_probability,
            "risk_band": p.risk_band,
            "confidence": p.confidence,
            "uncertainty": p.uncertainty,
            "is_ood": p.is_ood,
            "ood_score": p.ood_score,
            "model_version": p.model_version or NOT_AVAILABLE,
            "feature_schema_version": p.feature_schema_version or NOT_AVAILABLE,
            "scoring_mode": p.scoring_mode or NOT_AVAILABLE,
            "scored_at": p.scored_at.isoformat() if p.scored_at else NOT_AVAILABLE,
        }

    def _explanation_block(self, e: Explanation | None) -> dict[str, Any]:
        if not e:
            return {"status": "not_available"}
        top_positive = sorted((e.top_positive_factors or {}).items(), key=lambda kv: abs(kv[1]), reverse=True)
        top_negative = sorted((e.top_negative_factors or {}).items(), key=lambda kv: abs(kv[1]), reverse=True)
        return {
            "method": e.method,
            "plain_language": e.plain_language_explanation,
            "top_risk_increasing": [{"feature": k, "contribution": v} for k, v in top_positive[:5]],
            "top_risk_reducing": [{"feature": k, "contribution": v} for k, v in top_negative[:5]],
        }

    # ------------------------------------------------------------------
    async def _data_reliability(self, application_id: str) -> dict[str, Any]:
        sources = (
            await self.db.execute(select(DataSource).where(DataSource.application_id == application_id))
        ).scalars().all()
        if not sources:
            return INSUFFICIENT
        rels = [s.reliability_score for s in sources if s.reliability_score is not None]
        miss = [s.missing_rate for s in sources if s.missing_rate is not None]
        validated = sum(1 for s in sources if s.validation_status == "validated")
        coverage_starts = [s.date_coverage_start for s in sources if s.date_coverage_start]
        coverage_ends = [s.date_coverage_end for s in sources if s.date_coverage_end]
        return {
            "status": "available",
            "source_count": len(sources),
            "sources": [
                {"type": s.source_type, "reliability_score": s.reliability_score, "record_count": s.record_count, "validation_status": s.validation_status}
                for s in sources
            ],
            "average_reliability_score": round(sum(rels) / len(rels), 4) if rels else NOT_AVAILABLE,
            "average_missing_rate": round(sum(miss) / len(miss), 4) if miss else NOT_AVAILABLE,
            "validation_pass_rate": round(validated / len(sources), 4),
            "total_records": sum((s.record_count or 0) for s in sources),
            "date_coverage_start": min(coverage_starts).isoformat() if coverage_starts else NOT_AVAILABLE,
            "date_coverage_end": max(coverage_ends).isoformat() if coverage_ends else NOT_AVAILABLE,
        }

    async def _transactions(self, application_id: str) -> list[Transaction]:
        return list(
            (
                await self.db.execute(
                    select(Transaction).join(DataSource, Transaction.data_source_id == DataSource.id).where(DataSource.application_id == application_id)
                )
            ).scalars().all()
        )

    async def _cash_flow(self, application: Application) -> dict[str, Any]:
        txns = await self._transactions(application.id)
        active = [t for t in txns if not t.is_excluded]
        if not active:
            return INSUFFICIENT
        records = [
            {"date": t.transaction_date, "amount": t.amount, "transaction_type": t.direction, "description": t.description, "category": t.analyst_category or t.category, "balance_after": None}
            for t in active
        ]
        f = FeatureEngineer.engineer_features(records)
        return {
            "status": "available",
            "note": "Analyst evidence / supplementary signal — NOT a trained PD predictor.",
            "average_monthly_income": round(f.get("monthly_income_mean", 0.0), 2),
            "income_volatility": round(f.get("monthly_income_std", 0.0), 2),
            "average_monthly_expense": round(f.get("monthly_expense_mean", 0.0), 2),
            "expense_volatility": round(f.get("monthly_expense_std", 0.0), 2),
            "net_monthly_cashflow": round(f.get("net_monthly_cashflow", 0.0), 2),
            "cashflow_volatility": round(f.get("cashflow_volatility", 0.0), 2),
            "average_balance": round(f.get("avg_balance", 0.0), 2),
            "minimum_balance": round(f.get("min_balance", 0.0), 2),
            "overdraft_count": int(f.get("overdraft_count", 0)),
            "savings_rate": round(f.get("savings_rate", 0.0), 4),
            "liquidity_buffer_months": round(f.get("buffer_months", 0.0), 2),
            "transaction_count": int(f.get("transaction_count", 0)),
            "days_of_data": int(f.get("days_of_data", 0)),
        }

    async def _integrity_alerts(self, application: Application, borrower: Borrower | None) -> dict[str, Any]:
        # Persisted alerts.
        persisted = (
            await self.db.execute(select(IntegrityAlert).where(IntegrityAlert.application_id == application.id))
        ).scalars().all()
        alerts = [
            {"type": a.alert_type, "severity": a.severity, "description": a.description, "status": a.status, "source": "persisted"}
            for a in persisted
        ]
        # Deterministic computed checks (fraud/integrity risk — SEPARATE from credit risk).
        txns = [t for t in await self._transactions(application.id) if not t.is_excluded]
        if txns:
            seen = set()
            dup = 0
            for t in txns:
                key = (t.transaction_date, round(float(t.amount), 2), (t.description or "").strip().lower())
                if key in seen:
                    dup += 1
                seen.add(key)
            if dup:
                alerts.append({"type": "duplicate_transaction", "severity": "medium", "description": f"{dup} exact-duplicate transaction(s) detected.", "status": "open", "source": "computed"})
            # Declared-vs-observed income mismatch.
            if borrower and borrower.monthly_income_declared:
                f = FeatureEngineer.engineer_features(
                    [{"date": t.transaction_date, "amount": t.amount, "transaction_type": t.direction, "description": t.description, "category": t.category, "balance_after": None} for t in txns]
                )
                observed = f.get("monthly_income_mean", 0.0)
                declared = float(borrower.monthly_income_declared)
                if observed > 0 and declared > 0 and (abs(observed - declared) / declared) > 0.4:
                    alerts.append({"type": "income_mismatch", "severity": "medium", "description": f"Declared monthly income (RM {declared:,.0f}) differs from observed (RM {observed:,.0f}) by >40%.", "status": "open", "source": "computed"})
        return {"status": "available", "count": len(alerts), "alerts": alerts}

    def _model_agreement(self, p: Prediction | None) -> dict[str, Any]:
        # Only one inference-compatible production model exists. The 2.1.0
        # Home Credit challenger has an incompatible feature contract/scale, so a
        # valid agreement comparison cannot be made (do not compare incompatible
        # models as interchangeable).
        return {
            "status": "insufficient_data",
            "reason": "Only one inference-compatible model (2.0.0) is active. The 2.1.0-challenger uses an incompatible feature contract/scale, so a valid multi-model agreement cannot be computed.",
            "active_model_pd": p.probability_of_default if p else NOT_AVAILABLE,
        }

    async def _timeline(self, application: Application) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for label, ts in [
            ("application_created", application.created_at),
            ("application_submitted", application.submitted_at),
            ("application_scored", application.scored_at),
            ("decision_recorded", application.decided_at),
        ]:
            if ts:
                events.append({"event": label, "at": ts.isoformat(), "source": "application"})
        logs = (
            await self.db.execute(
                select(AuditLog).where(AuditLog.resource_id == application.id).order_by(AuditLog.created_at)
            )
        ).scalars().all()
        for log in logs:
            events.append({"event": log.action, "at": log.created_at.isoformat() if log.created_at else None, "source": "audit"})
        decisions = (
            await self.db.execute(select(Decision).where(Decision.application_id == application.id).order_by(Decision.decided_at))
        ).scalars().all()
        for d in decisions:
            events.append({"event": f"decision:{d.decision}", "at": d.decided_at.isoformat() if d.decided_at else None, "source": "decision"})
        events.sort(key=lambda e: e["at"] or "")
        return events
