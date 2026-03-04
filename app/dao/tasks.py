from app.dao.base import BaseDAO
from app.models.tasks import Task


class TaskDAO(BaseDAO):
    model = Task