import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from carradar.db.models import Base
from carradar.shared.config import settings


def run(conn):
    context.configure(connection=conn, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def main():
    eng = create_async_engine(settings.database_url)
    async with eng.connect() as c:
        await c.run_sync(run)
    await eng.dispose()


asyncio.run(main())
