from datetime import date, datetime, time, timedelta, timezone
from typing import List
from sqlalchemy import select, func
from app.database import sync_session_maker
from app.dao.base import BaseDAO
from app.models.tasks import Task


class TaskDAO(BaseDAO):
    model = Task
        
    @staticmethod
    def get_completed_yesterday(user_id: int, target_date: date) -> List[Task]:
        with sync_session_maker() as session:
            start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
            end = datetime.combine(target_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
            
            stmt = select(Task).where(
                Task.owner_id == user_id,
                Task.is_completed == True,
                Task.completed_at >= start,
                Task.completed_at < end
            )
            result = session.execute(stmt)
            return list(result.unique().scalars().all())

    @classmethod
    def count_pending_sync(cls, owner_id: int) -> int:
        with sync_session_maker() as session:
            stmt = select(func.count(cls.model.id)).where(
                cls.model.owner_id == owner_id,
                cls.model.is_completed == False
            )
            result = session.execute(stmt)
            return result.scalar() or 0

    @classmethod
    def find_pending_titles_sync(cls, owner_id: int, limit: int = 5) -> List[str]:
        with sync_session_maker() as session:
            stmt = select(cls.model.title).where(
                cls.model.owner_id == owner_id,
                cls.model.is_completed == False
            ).limit(limit)
            result = session.execute(stmt)
            return list(result.scalars().all())
