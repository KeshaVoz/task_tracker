from datetime import date, datetime, timezone
from typing import Any
from app.dao.tasks import TaskDAO
from app.schemas.email import SDailyReportData
from app.schemas.tasks import STaskIn, STaskOut, STaskUpdate
from app.exceptions.base import AppServiceException
from fastapi import status


class TaskService:
    @staticmethod
    async def create_task(task: STaskIn, owner_id: int) -> STaskOut:
        task_data = task.model_dump()
        task_data['owner_id'] = owner_id
        return await TaskDAO.add(**task_data)
    
    @staticmethod
    async def update_task(task_id: int, task_data: STaskUpdate, owner_id: int) -> STaskOut:
        task = await TaskDAO.find_one_or_none(id=task_id, owner_id=owner_id)
        if not task:
            raise AppServiceException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Task not found or you don't have permission to modify it."
            )
        
        update_dict = task_data.model_dump(exclude_unset=True)
        
        if "is_completed" in update_dict:
            if update_dict["is_completed"]:
                update_dict["completed_at"] = datetime.now(timezone.utc)
            else:
                update_dict["completed_at"] = None

        await TaskDAO.update({'id': task_id, 'owner_id': owner_id}, update_dict)
        return await TaskDAO.find_one_or_none(id=task_id, owner_id=owner_id)
    
    @staticmethod
    async def delete_task(task_id: int, owner_id: int) -> bool:
        task = await TaskDAO.find_one_or_none(id=task_id, owner_id=owner_id)
        if not task:
            raise AppServiceException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Task not found or you don't have permission to delete it."
            )
            
        return await TaskDAO.delete(id=task_id, owner_id=owner_id)
    
    @staticmethod
    def get_user_daily_analytics(user_id: int, yesterday: date) -> SDailyReportData:
        total_pending = TaskDAO.count_pending_sync(owner_id=user_id)
        pending_titles = TaskDAO.find_pending_titles_sync(owner_id=user_id, limit=5)
        
        completed_tasks = TaskDAO.get_completed_yesterday(user_id, yesterday)
        completed_titles = [task.title for task in completed_tasks]

        return SDailyReportData(
            total_pending=total_pending,
            pending_titles=pending_titles,
            completed_count=len(completed_tasks),
            completed_titles=completed_titles,
        )
