from app.dao.base import BaseDAO
from app.models.users import User


class UserDAO(BaseDAO):
    model = User