from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_accessible_application, get_current_user, require_roles
from app.models.decision import Decision
from app.models.user import User, UserRole
from app.schemas.decision import DecisionCreate, DecisionOut
from app.services.audit_service import add_audit_log

router = APIRouter(prefix="/applications/{application_id}/decisions", tags=["Decisions"])


@router.post("", response_model=DecisionOut, status_code=201)
async def create_decision(
    application_id: str,
    data: DecisionCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.CREDIT_ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    application = await get_accessible_application(db, application_id, current_user, staff_only=True)
    decision = Decision(
        application_id=application_id,
        analyst_id=current_user.id,
        decision=data.decision,
        reason=data.reason,
        override_type=data.override_type,
        override_reason=data.override_reason,
        approved_amount=data.approved_amount,
        approved_term_months=data.approved_term_months,
        conditions=data.conditions,
    )
    db.add(decision)
    await db.flush()
    application.status = data.decision
    application.decided_at = datetime.utcnow()
    add_audit_log(
        db,
        user_id=current_user.id,
        action="decision.created",
        resource_type="decision",
        resource_id=decision.id,
        details={"application_id": application_id, "decision": data.decision},
    )
    await db.commit()
    await db.refresh(decision)
    return decision


@router.get("", response_model=list[DecisionOut])
async def list_decisions(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_accessible_application(db, application_id, current_user)
    result = await db.execute(
        select(Decision)
        .where(Decision.application_id == application_id)
        .order_by(Decision.decided_at.desc())
    )
    return list(result.scalars().all())
