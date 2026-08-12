"""Seed the database with test users for development."""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import async_session
from app.models.user import User, UserRole
from app.models.borrower import Borrower, BorrowerType
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

TEST_USERS = [
    {
        "email": "analyst@lender.example",
        "password": "Password123!",
        "full_name": "Alex Morgan",
        "role": UserRole.CREDIT_ANALYST,
    },
    {
        "email": "borrower@example.com",
        "password": "Password123!",
        "full_name": "Jamie Rivera",
        "role": UserRole.BORROWER,
    },
    {
        "email": "admin@mycreditlens.com",
        "password": "Password123!",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
    },
]


async def seed():
    async with async_session() as db:
        for user_data in TEST_USERS:
            # Check if user already exists
            from sqlalchemy import select
            result = await db.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                print(f"User already exists: {user_data['email']}")
                continue

            user = User(
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
            )
            db.add(user)
            await db.flush()

            if user_data["role"] == UserRole.BORROWER:
                db.add(Borrower(user_id=user.id, borrower_type=BorrowerType.INDIVIDUAL))

            print(f"Created user: {user_data['email']} ({user_data['role'].value})")

        await db.commit()
        print("\nSeed complete!")


if __name__ == "__main__":
    asyncio.run(seed())