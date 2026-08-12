from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_accessible_application, get_current_user
from app.models.consent import Consent
from app.models.user import User, UserRole
from app.schemas.consent import ConsentCreate, ConsentOut
from app.services.audit_service import add_audit_log

router = APIRouter(prefix="/applications/{application_id}/consents", tags=["Consents"])


@router.get("", response_model=list[ConsentOut])
async def list_consents(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_accessible_application(db, application_id, current_user)
    result = await db.execute(
        select(Consent).where(Consent.application_id == application_id).order_by(Consent.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=ConsentOut, status_code=status.HTTP_201_CREATED)
async def grant_consent(
    application_id: str,
    data: ConsentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != UserRole.BORROWER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the borrower can grant consent")
    await get_accessible_application(db, application_id, current_user)
    result = await db.execute(
        select(Consent).where(
            Consent.application_id == application_id,
            Consent.data_source_type == data.data_source_type,
        )
    )
    consent = result.scalar_one_or_none()
    now = datetime.utcnow()
    if consent:
        consent.granted = True
        consent.granted_at = now
        consent.revoked_at = None
        consent.consent_version = "1.0"
    else:
        consent = Consent(
            application_id=application_id,
            data_source_type=data.data_source_type,
            granted=True,
            granted_at=now,
            consent_version="1.0",
        )
        db.add(consent)
    add_audit_log(
        db,
        user_id=current_user.id,
        action="consent.granted",
        resource_type="consent",
        resource_id=consent.id,
        details={"application_id": application_id, "data_source_type": data.data_source_type},
    )
    await db.commit()
    await db.refresh(consent)
    return consent


@router.post("/{consent_id}/revoke", response_model=ConsentOut)
async def revoke_consent(
    application_id: str,
    consent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != UserRole.BORROWER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the borrower can revoke consent")
    await get_accessible_application(db, application_id, current_user)
    result = await db.execute(
        select(Consent).where(Consent.id == consent_id, Consent.application_id == application_id)
    )
    consent = result.scalar_one_or_none()
    if not consent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent not found")
    consent.granted = False
    consent.revoked_at = datetime.utcnow()
    add_audit_log(
        db,
        user_id=current_user.id,
        action="consent.revoked",
        resource_type="consent",
        resource_id=consent.id,
        details={"application_id": application_id},
    )
    await db.commit()
    await db.refresh(consent)
    return consent
