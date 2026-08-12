from sqlalchemy.ext.asyncio import async_sessionmaker
from .engine import engine

sessionLocal = async_sessionmaker(
  bind=engine,
  expire_on_commit=False
)

async def get_db():
  async with sessionLocal() as session:
    yield session