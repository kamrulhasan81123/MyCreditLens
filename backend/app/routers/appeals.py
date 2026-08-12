from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_accessible_application, get_current_user, require_roles
from app.models.appeal import Appeal
from app.models.user import User, UserRole
from app.schemas.appeal import AppealCreate, AppealOut, AppealUpdate
from app.services.audit_service import add_audit_log

router = APIRouter(prefix="/applications/{application_id}/appeals", tags=["Appeals"])


@router.post("", response_model=AppealOut, status_code=201)
async def create_appeal(
    application_id: str,
    data: AppealCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != UserRole.BORROWER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the borrower can appeal")
    application = await get_accessible_application(db, application_id, current_user)
    if application.status not in {"approved", "rejected", "information_requested"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This application is not eligible for appeal")
    existing = await db.execute(
        select(Appeal).where(Appeal.application_id == application_id, Appeal.status.in_(["pending", "under_review"]))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An active appeal already exists")
    appeal = Appeal(application_id=application_id, reason=data.reason, evidence=data.evidence, status="pending")
    db.add(appeal)
    await db.flush()
    application.status = "appealed"
    add_audit_log(
        db,
        user_id=current_user.id,
        action="appeal.created",
        resource_type="appeal",
        resource_id=appeal.id,
        details={"application_id": application_id},
    )
    await db.commit()
    await db.refresh(appeal)
    return appeal


@router.get("", response_model=list[AppealOut])
async def list_appeals(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_accessible_application(db, application_id, current_user)
    result = await db.execute(
        select(Appeal).where(Appeal.application_id == application_id).order_by(Appeal.created_at.desc())
    )
    return list(result.scalars().all())


@router.patch("/{appeal_id}", response_model=AppealOut)
async def review_appeal(
    application_id: str,
    appeal_id: str,
    data: AppealUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.COMPLIANCE_REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    await get_accessible_application(db, application_id, current_user, staff_only=True)
    result = await db.execute(select(Appeal).where(Appeal.id == appeal_id, Appeal.application_id == application_id))
    appeal = result.scalar_one_or_none()
    if not appeal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appeal not found")
    appeal.status = data.status
    appeal.reviewer_id = current_user.id
    appeal.reviewer_notes = data.reviewer_notes
    appeal.resolution = data.resolution
    if data.status in {"resolved", "rejected"}:
        appeal.resolved_at = datetime.utcnow()
    add_audit_log(
        db,
        user_id=current_user.id,
        action="appeal.reviewed",
        resource_type="appeal",
        resource_id=appeal.id,
        details={"application_id": application_id, "status": data.status},
    )
    await db.commit()
    await db.refresh(appeal)
    return appeal
