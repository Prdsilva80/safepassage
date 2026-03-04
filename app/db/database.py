import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.database_url_async,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

async def create_all_tables():
    from app.models import models  # noqa: F401
    for attempt in range(30):
        try:
            async with engine.connect() as conn:
                await conn.execute(__import__('sqlalchemy').text("SELECT 1"))
            break
        except Exception as e:
            print(f"Waiting for DB (attempt {attempt+1}/30): {e}")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Could not connect to database after 30 attempts")

    # Create tables one by one, ignoring already-exists errors
    async with engine.begin() as conn:
        await conn.run_sync(_create_tables_safe)
    print("Database tables ready")

def _create_tables_safe(conn):
    from app.db.database import Base
    for table in Base.metadata.sorted_tables:
        try:
            table.create(conn, checkfirst=True)
            print(f"  Table {table.name}: OK")
        except Exception as e:
            print(f"  Table {table.name}: {e}")
