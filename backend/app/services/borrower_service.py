from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.borrower import Borrower
from app.schemas.borrower import BorrowerCreate, BorrowerUpdate
from app.models.user import User


class BorrowerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, data: BorrowerCreate) -> Borrower:
        existing = await self.find_by_user_id(user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Borrower profile already exists",
            )
        borrower = Borrower(user_id=user_id, **data.model_dump())
        self.db.add(borrower)
        await self.db.commit()
        await self.db.refresh(borrower)
        return borrower

    async def find_by_user_id(self, user_id: str) -> Borrower | None:
        result = await self.db.execute(select(Borrower).where(Borrower.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> Borrower:
        borrower = await self.find_by_user_id(user_id)
        if not borrower:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Borrower profile not found",
            )
        return borrower

    async def get_by_id(self, borrower_id: str) -> Borrower:
        result = await self.db.execute(select(Borrower).where(Borrower.id == borrower_id))
        borrower = result.scalar_one_or_none()
        if not borrower:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Borrower not found",
            )
        return borrower

    async def update(self, user_id: str, data: BorrowerUpdate) -> Borrower:
        borrower = await self.get_by_user_id(user_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(borrower, key, value)
        await self.db.commit()
        await self.db.refresh(borrower)
        return borrower

    async def list_all(self, page: int, page_size: int, search: str | None = None) -> dict:
        filters = []
        if search:
            value = f"%{search.strip()}%"
            filters.append(or_(User.full_name.ilike(value), User.email.ilike(value), Borrower.id.ilike(value)))
        total = (
            await self.db.execute(
                select(func.count()).select_from(Borrower).join(User).where(*filters)
            )
        ).scalar_one()
        result = await self.db.execute(
            select(Borrower)
            .join(User)
            .where(*filters)
            .order_by(Borrower.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return {
            "items": list(result.scalars().all()),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
