from datetime import date, timedelta
from typing import List
from sqlalchemy import and_, select
from app.database import sync_session_maker
from app.dao.base import BaseDAO
from app.models.tasks import Task


class TaskDAO(BaseDAO):
    model = Task
        
    @staticmethod
    def get_completed_yesterday(user_id: int, target_date: date) -> List[Task]:
        with sync_session_maker() as session:
            start = target_date
            end = target_date + timedelta(days=1)
            stmt = select(Task).where(
                and_(
                    Task.owner_id == user_id,
                    Task.is_completed == True,
                    Task.completed_at >= start,
                    Task.completed_at < end
                )
            )
            result = session.execute(stmt)
            return list(result.unique().scalars().all())