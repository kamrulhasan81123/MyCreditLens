from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.prediction import ScoreRequest, ScoreResponse, PredictionOut
from app.schemas.explanation import ExplanationOut, ExplanationRequest
from app.services.scoring_service import ScoringService
from app.dependencies import get_accessible_application, get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.model import MLModel

router = APIRouter(tags=["AI Scoring"])


@router.post("/applications/{application_id}/score", response_model=ScoreResponse)
async def score_application(
    application_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.CREDIT_ANALYST)),
    db: AsyncSession = Depends(get_db),
    model_version: str | None = None,
):
    """Run AI scoring on an application.

    Returns the persisted prediction. `model_version` is the real human-readable
    model version string (not the model UUID).
    """
    await get_accessible_application(db, application_id, current_user, staff_only=True)
    service = ScoringService(db)
    prediction = await service.score_application(application_id, model_version)
    model = await db.get(MLModel, prediction.model_id)
    has_explanation = await service.has_explanation(prediction.id)
    return ScoreResponse(
        prediction_id=prediction.id,
        application_id=prediction.application_id,
        probability_of_default=prediction.probability_of_default,
        calibrated_probability=prediction.calibrated_probability,
        raw_probability=prediction.raw_probability,
        risk_band=prediction.risk_band,
        confidence=prediction.confidence,
        uncertainty=prediction.uncertainty,
        model_id=prediction.model_id,
        model_version=prediction.model_version or (model.version if model else "unknown"),
        model_name=model.model_name if model else None,
        feature_schema_version=prediction.feature_schema_version,
        feature_version=prediction.feature_schema_version,
        scoring_mode=prediction.scoring_mode,
        is_ood=prediction.is_ood,
        ood_score=prediction.ood_score,
        explanation_available=has_explanation,
        scored_at=prediction.scored_at,
    )


@router.get("/applications/{application_id}/predictions", response_model=PredictionOut)
async def get_prediction(
    application_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest prediction for an application."""
    await get_accessible_application(db, application_id, current_user)
    service = ScoringService(db)
    return await service.get_latest_prediction(application_id)


@router.get("/applications/{application_id}/explanations", response_model=ExplanationOut)
async def get_explanation(
    application_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest explanation for an application."""
    await get_accessible_application(db, application_id, current_user)
    service = ScoringService(db)
    return await service.get_latest_explanation(application_id)


@router.get("/applications/{application_id}/decision-room")
async def get_decision_room(
    application_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.CREDIT_ANALYST, UserRole.COMPLIANCE_REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    """Consolidated, real Decision Room payload: application, scoring, SHAP,
    data reliability, cash-flow analytics, integrity alerts, model agreement,
    and timeline. Uncomputable values are `not_available`/`insufficient_data` —
    never fabricated. Staff-only."""
    from app.services.decision_room_service import DecisionRoomService

    application = await get_accessible_application(db, application_id, current_user, staff_only=True)
    return await DecisionRoomService(db).build(application)
