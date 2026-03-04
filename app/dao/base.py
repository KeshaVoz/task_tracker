from sqlalchemy import delete, select, insert, update
from typing import Any, Dict, Optional, List
from app.database import async_session_maker


class BaseDAO:
    model = None

    @classmethod
    async def add(cls, **data: Any) -> Any:
        async with async_session_maker() as session:
            stmt = insert(cls.model).values(**data).returning(cls.model)
            result = await session.execute(stmt)
            await session.commit()
            obj_row = result.fetchone()
            return obj_row[0] if obj_row else None

    @classmethod
    async def find_one_or_none(cls, **filter_by: Any) -> Optional[Any]:
        async with async_session_maker() as session:
            stmt = select(cls.model)
            if filter_by:
                stmt = stmt.filter_by(**filter_by)
            result = await session.execute(stmt)
            return result.unique().scalar_one_or_none()

    @classmethod
    async def find_all(cls, **filter_by: Any) -> List[Any]:
        async with async_session_maker() as session:
            stmt = select(cls.model)
            if filter_by:
                stmt = stmt.filter_by(**filter_by)
            result = await session.execute(stmt)
            return list(result.unique().scalars().all())

    @classmethod
    async def update(cls, filter_by: Dict[str, Any], update_data: Dict[str, Any]) -> bool:
        async with async_session_maker() as session:
            stmt = update(cls.model).filter_by(**filter_by).values(**update_data)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
        
    @classmethod
    async def delete(cls, **filter_by: Any) -> bool:
        async with async_session_maker() as session:
            stmt = delete(cls.model).filter_by(**filter_by)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
