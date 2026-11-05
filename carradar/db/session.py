from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from carradar.shared.config import settings

engine = create_async_engine(settings.database_url, pool_size=10, pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False)
