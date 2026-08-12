from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_accessible_application, get_current_user, require_roles
from app.models.report import Report
from app.models.user import User, UserRole
from app.schemas.report import ReportCreate, ReportOut
from app.services.audit_service import add_audit_log

router = APIRouter(prefix="/applications/{application_id}/reports", tags=["Reports"])


@router.post("", response_model=ReportOut, status_code=201)
async def create_report(
    application_id: str,
    data: ReportCreate,
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.CREDIT_ANALYST, UserRole.COMPLIANCE_REVIEWER)
    ),
    db: AsyncSession = Depends(get_db),
):
    await get_accessible_application(db, application_id, current_user, staff_only=True)
    report = Report(
        application_id=application_id,
        report_type=data.report_type,
        title=data.title,
        generated_by=current_user.id,
        content=data.content or {},
        summary=data.summary,
    )
    db.add(report)
    await db.flush()
    add_audit_log(
        db,
        user_id=current_user.id,
        action="report.created",
        resource_type="report",
        resource_id=report.id,
        details={"application_id": application_id, "report_type": data.report_type},
    )
    await db.commit()
    await db.refresh(report)
    return report


@router.get("", response_model=list[ReportOut])
async def list_reports(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_accessible_application(db, application_id, current_user)
    result = await db.execute(
        select(Report).where(Report.application_id == application_id).order_by(Report.generated_at.desc())
    )
    return list(result.scalars().all())
