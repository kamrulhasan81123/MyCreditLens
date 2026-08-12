from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.counterfactual import CounterfactualGenerator
from app.ai.fairness_auditor import FairnessAuditor
from app.ai.model_monitor import ModelMonitor
from app.ai.stress_tester import StressTester
from app.database import get_db
from app.dependencies import get_accessible_application, require_roles
from app.models.fairness import FairnessMetric
from app.models.user import User, UserRole
from app.schemas.ai import (
    CounterfactualRequest,
    DriftEvaluationRequest,
    FairnessEvaluationRequest,
    PerformanceEvaluationRequest,
)
from app.services.scoring_service import ScoringService

router = APIRouter(tags=["AI Governance"])


@router.post("/applications/{application_id}/counterfactuals")
async def counterfactuals(
    application_id: str,
    data: CounterfactualRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.CREDIT_ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """What-if analysis over the SAME feature contract as scoring.

    Expected model/schema/readiness problems surface as structured 409/422/503
    (via the shared adapter path), never as a generic 500.
    """
    await get_accessible_application(db, application_id, current_user, staff_only=True)
    _, _, runtime, features = await ScoringService(db).prepare_scoring_inputs(application_id)
    return CounterfactualGenerator.generate(
        runtime, features, target_probability=data.target_probability, limit=data.limit
    )


@router.post("/applications/{application_id}/stress-tests")
async def stress_tests(
    application_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.CREDIT_ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """Adverse-scenario re-scoring over the SAME feature contract as scoring."""
    await get_accessible_application(db, application_id, current_user, staff_only=True)
    _, _, runtime, features = await ScoringService(db).prepare_scoring_inputs(application_id)
    return StressTester.run(runtime, features)


@router.post("/fairness/evaluate")
async def evaluate_fairness(
    data: FairnessEvaluationRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    report = FairnessAuditor.evaluate(
        data.labels,
        data.probabilities,
        data.groups,
        threshold=data.threshold,
        minimum_group_size=data.minimum_group_size,
    )
    if report.get("status") == "evaluated":
        for name, value in report["disparities"].items():
            if value is None:
                continue
            db.add(
                FairnessMetric(
                    model_id=data.model_id,
                    metric_name=name,
                    metric_value=float(value),
                    threshold=0.8 if name == "disparate_impact_ratio" else 0.1,
                    is_acceptable=(value >= 0.8 if name == "disparate_impact_ratio" else value <= 0.1),
                    group_breakdown=report["group_metrics"],
                )
            )
        await db.commit()
    return report


@router.post("/monitoring/drift/evaluate")
async def evaluate_drift(
    data: DriftEvaluationRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_REVIEWER)),
):
    return ModelMonitor.drift_report(data.reference, data.current)


@router.post("/monitoring/performance/evaluate")
async def evaluate_performance(
    data: PerformanceEvaluationRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_REVIEWER)),
):
    return ModelMonitor.performance(data.labels, data.probabilities, data.threshold)
