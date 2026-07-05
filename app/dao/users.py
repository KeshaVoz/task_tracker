from typing import List
from sqlalchemy import select
from app.dao.base import BaseDAO
from app.models.users import User
from app.database import sync_session_maker

class UserDAO(BaseDAO):
    model = User

    @classmethod
    def find_all_ids_chunk(cls, limit: int = 500, offset: int = 0) -> List[int]:
        with sync_session_maker() as session:
            stmt = select(cls.model.id).limit(limit).offset(offset).order_by(cls.model.id)
            result = session.execute(stmt)
            return list(result.scalars().all())