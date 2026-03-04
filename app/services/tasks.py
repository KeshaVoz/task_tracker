from typing import Optional
from app.dao.tasks import TaskDAO
from app.schemas.tasks import STaskIn

class TaskService:
    @staticmethod
    async def create_task(task: STaskIn, owner_id: int):
        task_data = task.model_dump()
        task_data['owner_id'] = owner_id
        return await TaskDAO.add(**task_data)
    
    @staticmethod
    async def update_task(task_id: int, task: STaskIn, owner_id: int) -> Optional[dict]:
        update_data = task.model_dump(exclude_unset=True)
        updated = await TaskDAO.update({'id': task_id, 'owner_id': owner_id}, update_data)
        if updated:
            return await TaskDAO.find_one_or_none(id=task_id, owner_id=owner_id)
        return None
    
    @staticmethod
    async def change_is_completed(task_id: int, is_completed: bool, owner_id: int) -> Optional[dict]:
        updated = await TaskDAO.update(
            {'id': task_id, 'owner_id': owner_id}, 
            {'is_completed': is_completed}
        )
        if updated:
            return await TaskDAO.find_one_or_none(id=task_id, owner_id=owner_id)
        return None
    
    @staticmethod
    async def delete_task(task_id: int, owner_id: int) -> bool:
        return await TaskDAO.delete(id=task_id, owner_id=owner_id)