from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .database import Session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with Session() as session:
        yield session
