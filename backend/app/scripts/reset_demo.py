import asyncio

from sqlalchemy import delete

from app.database import async_session
from app.models.application import Application
from app.models.borrower import Borrower
from app.models.user import User


async def main() -> None:
    async with async_session() as db:
        await db.execute(delete(Application))
        await db.execute(delete(Borrower))
        await db.execute(delete(User).where(User.email.like("%@mycreditlens.local")))
        await db.commit()
    print("Demo data reset completed.")


if __name__ == "__main__":
    asyncio.run(main())
