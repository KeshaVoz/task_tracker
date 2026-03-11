from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

sync_engine = create_engine(
    settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'),  
    pool_pre_ping=True,
    pool_recycle=300
)
sync_session_maker = sessionmaker(sync_engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True