"""Read-only model / monitoring / fairness insight endpoints.

Safe by construction: no filesystem paths, secrets, or env vars are returned.
Monitoring never fabricates production performance; fairness/calibration are
development-grade measurements on the model's held-out evaluation split.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.runtime import ArtifactUnavailableError, load_credit_runtime
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.services.insights_service import InsightsService, safe_model_metadata

router = APIRouter(tags=["Model & Monitoring"])


def _active_runtime():
    artifact_dir = settings.resolved_model_artifact_path
    if not (artifact_dir / "manifest.json").is_file():
        raise HTTPException(status_code=503, detail="No active model bundle is available")
    try:
        return load_credit_runtime(artifact_dir)
    except ArtifactUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/models/active")
async def get_active_model(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Safe, read-only active-model metadata (any authenticated user)."""
    return await InsightsService(db).active_model()


@router.get("/models/metadata")
async def get_model_metadata(current_user: User = Depends(get_current_user)):
    """Model-card-safe metadata straight from the active bundle."""
    return safe_model_metadata(_active_runtime())


@router.post("/models/registry/sync")
async def sync_model_registry(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Register/refresh the active bundle in the ml_models table (admin only)."""
    row = await InsightsService(db).sync_registry()
    return {"model_id": row.id, "model_name": row.model_name, "version": row.version, "is_active": row.is_active}


@router.get("/monitoring/summary")
async def monitoring_summary(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.CREDIT_ANALYST, UserRole.COMPLIANCE_REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    return await InsightsService(db).monitoring_summary()


@router.get("/fairness/age-band-audit")
async def age_band_fairness(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    return InsightsService(db).age_band_fairness(_active_runtime())


@router.get("/calibration/segments")
async def calibration_segments(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    return InsightsService(db).calibration_by_segment(_active_runtime())
