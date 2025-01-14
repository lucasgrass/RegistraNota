import asyncio
from app.core.db import engine, init_db
from sqlalchemy.ext.asyncio import AsyncSession


async def init():
    async with AsyncSession(engine) as session:
        await init_db(session)


def main():
    print("Creating initial data")
    asyncio.run(init())
    print("Finished initial data")


if __name__ == "__main__":
    main()