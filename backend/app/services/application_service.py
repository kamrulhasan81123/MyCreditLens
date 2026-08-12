import uuid
from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.application import Application
from app.models.borrower import Borrower
from app.models.consent import Consent
from app.models.user import User, UserRole
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.services.audit_service import add_audit_log


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, current_user: User, data: ApplicationCreate) -> Application:
        if current_user.role != UserRole.BORROWER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only borrowers can create applications")
        borrower = await self._get_borrower_for_user(current_user.id)
        if not borrower:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Borrower profile required before creating an application",
            )
        application = Application(
            borrower_id=borrower.id,
            reference=f"APP-{uuid.uuid4().hex[:8].upper()}",
            purpose=data.purpose,
            loan_intent=data.loan_intent,
            requested_amount=data.requested_amount,
            requested_term_months=data.requested_term_months,
            status="draft",
        )
        self.db.add(application)
        await self.db.flush()
        add_audit_log(
            self.db,
            user_id=current_user.id,
            action="application.created",
            resource_type="application",
            resource_id=application.id,
            details={"reference": application.reference},
        )
        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def get_by_id(self, application_id: str, current_user: User) -> Application:
        if current_user.role == UserRole.BORROWER:
            borrower = await self._get_borrower_for_user(current_user.id)
            result = await self.db.execute(
                select(Application).where(
                    Application.id == application_id,
                    Application.borrower_id == borrower.id if borrower else False,
                )
            )
        else:
            result = await self.db.execute(select(Application).where(Application.id == application_id))
        application = result.scalar_one_or_none()
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )
        return application

    async def list_for_user(self, current_user: User, page: int, page_size: int, status_filter: str = None) -> dict:
        filters = []
        if current_user.role == UserRole.BORROWER:
            borrower = await self._get_borrower_for_user(current_user.id)
            if not borrower:
                return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
            filters.append(Application.borrower_id == borrower.id)
        if status_filter:
            filters.append(Application.status == status_filter)
        total_result = await self.db.execute(select(func.count()).select_from(Application).where(*filters))
        total = total_result.scalar_one()
        items_result = await self.db.execute(
            select(Application)
            .where(*filters)
            .order_by(Application.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(items_result.scalars().all())
        total_pages = (total + page_size - 1) // page_size if page_size else 0
        return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}

    async def update(self, application_id: str, current_user: User, data: ApplicationUpdate) -> Application:
        if current_user.role != UserRole.BORROWER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the borrower can edit an application")
        application = await self.get_by_id(application_id, current_user)
        if application.status not in ("draft",):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft applications can be updated",
            )
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(application, key, value)
        add_audit_log(
            self.db,
            user_id=current_user.id,
            action="application.updated",
            resource_type="application",
            resource_id=application.id,
            details={"fields": list(data.model_dump(exclude_unset=True))},
        )
        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def submit(self, application_id: str, current_user: User) -> None:
        if current_user.role != UserRole.BORROWER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the borrower can submit an application")
        application = await self.get_by_id(application_id, current_user)
        if application.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft applications can be submitted",
            )
        consent_result = await self.db.execute(
            select(Consent).where(Consent.application_id == application.id, Consent.granted.is_(True))
        )
        if not consent_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="At least one active data consent is required before submission",
            )
        application.status = "submitted"
        application.submitted_at = datetime.utcnow()
        add_audit_log(
            self.db,
            user_id=current_user.id,
            action="application.submitted",
            resource_type="application",
            resource_id=application.id,
        )
        await self.db.commit()

    async def _get_borrower_for_user(self, user_id: str) -> Borrower | None:
        result = await self.db.execute(select(Borrower).where(Borrower.user_id == user_id))
        return result.scalar_one_or_none()
