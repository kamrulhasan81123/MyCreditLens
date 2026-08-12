from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.borrower import BorrowerCreate, BorrowerUpdate, BorrowerOut, BorrowerListOut
from app.services.borrower_service import BorrowerService
from app.dependencies import get_current_user, require_roles
from app.models.user import UserRole

router = APIRouter(prefix="/borrowers", tags=["Borrowers"])


@router.post("/", response_model=BorrowerOut, status_code=status.HTTP_201_CREATED)
async def create_borrower(
    data: BorrowerCreate,
    current_user=Depends(require_roles(UserRole.BORROWER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create the current user's borrower profile.

    Restricted to the borrower themselves (self-onboarding) and admins.
    Credit analysts and compliance reviewers review applications; they do not
    create borrower records, so they are refused with 403. Unauthenticated
    requests are rejected by the auth dependency with 401.
    """
    service = BorrowerService(db)
    return await service.create(current_user.id, data)


@router.get("/", response_model=BorrowerListOut)
async def list_borrowers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    current_user=Depends(require_roles(UserRole.ADMIN, UserRole.CREDIT_ANALYST, UserRole.COMPLIANCE_REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    return await BorrowerService(db).list_all(page, page_size, search)


@router.get("/me", response_model=BorrowerOut)
async def get_my_borrower_profile(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's borrower profile."""
    service = BorrowerService(db)
    return await service.get_by_user_id(current_user.id)


@router.put("/me", response_model=BorrowerOut)
async def update_my_borrower_profile(
    data: BorrowerUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's borrower profile."""
    service = BorrowerService(db)
    return await service.update(current_user.id, data)


@router.get("/{borrower_id}", response_model=BorrowerOut)
async def get_borrower(
    borrower_id: str,
    current_user=Depends(require_roles(UserRole.ADMIN, UserRole.CREDIT_ANALYST, UserRole.COMPLIANCE_REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    return await BorrowerService(db).get_by_id(borrower_id)
