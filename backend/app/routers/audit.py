from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_roles
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.audit import AuditLogOut

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("", response_model=list[AuditLogOut])
async def list_audit_logs(
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.CREDIT_ANALYST, UserRole.COMPLIANCE_REVIEWER)
    ),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if resource_type:
        filters.append(AuditLog.resource_type == resource_type)
    if resource_id:
        filters.append(AuditLog.resource_id == resource_id)
    result = await db.execute(
        select(AuditLog).where(*filters).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())
