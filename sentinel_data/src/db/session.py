# sentinel_data/src/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False, # Set to True to see SQL queries in logs
    future=True,
    pool_size=20,
    max_overflow=10
)

# Async Session Factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db():
    """Dependency for dependency injection."""
    async with AsyncSessionLocal() as session:
        yield session