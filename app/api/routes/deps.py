from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import engine


async def get_session() -> AsyncSession:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session