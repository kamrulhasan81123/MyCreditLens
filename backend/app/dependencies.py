from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.application import Application
from app.models.borrower import Borrower
from app.models.user import User, UserRole
from app.services.auth_service import AuthService, oauth2_scheme


STAFF_ROLES = {
    UserRole.ADMIN,
    UserRole.CREDIT_ANALYST,
    UserRole.COMPLIANCE_REVIEWER,
}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await AuthService(db).get_current_user(token)


def require_roles(*allowed_roles: UserRole) -> Callable:
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in set(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return dependency


async def get_accessible_application(
    db: AsyncSession,
    application_id: str,
    current_user: User,
    *,
    staff_only: bool = False,
) -> Application:
    if current_user.role in STAFF_ROLES:
        result = await db.execute(select(Application).where(Application.id == application_id))
    elif not staff_only and current_user.role == UserRole.BORROWER:
        result = await db.execute(
            select(Application)
            .join(Borrower, Application.borrower_id == Borrower.id)
            .where(Application.id == application_id, Borrower.user_id == current_user.id)
        )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application
