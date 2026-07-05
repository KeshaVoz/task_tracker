from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine = create_async_engine(settings.SUMMARY_DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True