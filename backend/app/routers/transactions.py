from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_accessible_application, get_current_user
from app.models.data_source import DataSource
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionOut

router = APIRouter(prefix="/applications/{application_id}/transactions", tags=["Transactions"])


@router.get("", response_model=list[TransactionOut])
async def list_transactions(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_accessible_application(db, application_id, current_user)
    result = await db.execute(
        select(Transaction)
        .join(DataSource, Transaction.data_source_id == DataSource.id)
        .where(DataSource.application_id == application_id)
        .order_by(Transaction.transaction_date.desc())
    )
    return list(result.scalars().all())
