from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.data_source import DataSourceOut, DataSourceUploadResponse
from app.services.data_source_service import DataSourceService
from app.dependencies import get_accessible_application, get_current_user
from app.models.user import User

router = APIRouter(tags=["Data Sources"])


@router.post("/applications/{application_id}/data-sources", response_model=DataSourceUploadResponse)
async def upload_data_source(
    application_id: str,
    source_type: str = Query(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload bank statement or transaction data file.

    Access is authorised with the same object-level rule as every other
    application-scoped route: the owning borrower, or any staff member
    permitted to review the application. Previously this path enforced an
    owner-only check, so authorised staff received a spurious 404.
    """
    application = await get_accessible_application(db, application_id, current_user)
    service = DataSourceService(db)
    return await service.upload(application, current_user, source_type, file)


@router.get("/applications/{application_id}/data-sources", response_model=list[DataSourceOut])
async def list_data_sources(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all data sources for an application."""
    await get_accessible_application(db, application_id, current_user)
    from sqlalchemy import select
    from app.models.data_source import DataSource

    result = await db.execute(
        select(DataSource)
        .where(DataSource.application_id == application_id)
        .order_by(DataSource.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/applications/{application_id}/data-sources/{data_source_id}/signed-url")
async def get_data_source_signed_url(
    application_id: str,
    data_source_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Short-lived signed URL for a stored data-source file. Object-level
    authorised (owner or permitted staff). Never exposes the service key."""
    from sqlalchemy import select
    from app.models.data_source import DataSource
    from app.services.storage_service import SupabaseStorageService

    await get_accessible_application(db, application_id, current_user)
    ds = (
        await db.execute(
            select(DataSource).where(DataSource.id == data_source_id, DataSource.application_id == application_id)
        )
    ).scalar_one_or_none()
    if not ds:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Data source not found")
    if not ds.storage_path or ds.storage_bucket in (None, "local"):
        return {"status": "not_available", "detail": "File is stored locally; no signed URL available."}
    return {"signed_url": SupabaseStorageService.signed_url(ds.storage_bucket, ds.storage_path), "expires_in": 3600}
