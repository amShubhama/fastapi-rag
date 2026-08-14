from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.core.config import settings

engine = create_async_engine(url=settings.database_url, echo=False, pool_pre_ping=True)
