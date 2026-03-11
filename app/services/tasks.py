from datetime import date, datetime, timezone
from typing import List, Optional
from app.dao.tasks import TaskDAO
from app.schemas.email import SDailyReportData, SEmailData
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
        update_data = {'is_completed': is_completed}
    
        if is_completed:
            update_data['completed_at'] = datetime.now(timezone.utc)
        else:
            update_data['completed_at'] = None
    
        updated = await TaskDAO.update({'id': task_id, 'owner_id': owner_id}, update_data)    
        if updated:
            return await TaskDAO.find_one_or_none(id=task_id, owner_id=owner_id)
        return None
    
    @staticmethod
    async def delete_task(task_id: int, owner_id: int) -> bool:
        return await TaskDAO.delete(id=task_id, owner_id=owner_id)
    
    @staticmethod
    def prepare_daily_report(user_id: int, yesterday: date) -> SDailyReportData:
        all_pending_tasks = TaskDAO.find_all_sync(owner_id=user_id, is_completed=False)
        total_pending = len(all_pending_tasks)
        pending_titles = [task.title for task in all_pending_tasks[:5]]
        completed_tasks = TaskDAO.get_completed_yesterday(user_id, yesterday)
        completed_titles = [task.title for task in completed_tasks]
        return SDailyReportData(
            total_pending=total_pending,
            pending_titles=pending_titles,
            completed_count=len(completed_tasks),
            completed_titles=completed_titles
        )

    @staticmethod
    def prepare_emails_from_report(user_email: str, report: SDailyReportData) -> List[SEmailData]:
        emails = []
        body_parts = []

        if report.completed_count > 0:
            titles = '\n'.join(report.completed_titles)
            body_parts.append(f'✅ You completed {report.completed_count} tasks yesterday:\n\n{titles}')
    
        if report.total_pending > 0:
            titles = '\n'.join(report.pending_titles)
            extra = f'\n... and {report.total_pending - 5} more' if len(report.pending_titles) < report.total_pending else ''
            body_parts.append(f"\n📝 You have {report.total_pending} pending tasks:\n\n{titles}{extra}")
    
        if body_parts:
            full_body = 'Task Tracker Daily Report:\n\n' + '\n\n'.join(body_parts)

            if report.completed_count > 0 and report.total_pending > 0:
                subject = f'📊 Report: {report.completed_count} completed, {report.total_pending} pending'
            elif report.completed_count > 0:
                subject = f'✅ You completed {report.completed_count} tasks yesterday!'
            else:
                subject = f'📝 You have {report.total_pending} pending tasks'
        
            emails.append(SEmailData(
                email=user_email,
                subject=subject,
                body=full_body
            ))
    
        return emails


    @staticmethod
    def prepare_welcome_email(user_email: str) -> SEmailData:
        return SEmailData(
            email=user_email,
            subject='Welcome to Task Tracker!',
            body="""Hello!

    You have successfully registered in Task Tracker.
    Now you can create and manage your tasks.
    """
        )

    