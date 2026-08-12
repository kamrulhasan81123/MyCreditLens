from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationOut, ApplicationListOut
from app.services.application_service import ApplicationService
from app.dependencies import get_current_user

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/", response_model=ApplicationOut, status_code=201)
async def create_application(
    data: ApplicationCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a new credit application."""
    service = ApplicationService(db)
    return await service.create(current_user, data)


@router.get("/", response_model=ApplicationListOut)
async def list_applications(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
):
    """List applications for the current user."""
    service = ApplicationService(db)
    return await service.list_for_user(current_user, page, page_size, status)


@router.get("/{application_id}", response_model=ApplicationOut)
async def get_application(
    application_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get application details."""
    service = ApplicationService(db)
    return await service.get_by_id(application_id, current_user)


@router.put("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: str,
    data: ApplicationUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an application."""
    service = ApplicationService(db)
    return await service.update(application_id, current_user, data)


@router.post("/{application_id}/submit")
async def submit_application(
    application_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit application for scoring."""
    service = ApplicationService(db)
    await service.submit(application_id, current_user)
    return {"message": "Application submitted for scoring"}
