from fastapi import APIRouter, Depends, HTTPException, status
from app.models.users import User
from app.schemas.tasks import STaskOut, STaskIn, STasksList
from app.dependencies import get_current_user
from app.dao.tasks import TaskDAO
from app.services.tasks import TaskService


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/all_tasks", response_model=STasksList)
async def get_tasks(current_user: User = Depends(get_current_user)):
    tasks = await TaskDAO.find_all(owner_id=current_user.id)
    return STasksList(tasks=tasks)


@router.post("/", response_model=STaskOut, status_code=201)
async def create_task(task_in: STaskIn,  current_user: User = Depends(get_current_user)):
    task = await TaskService.create_task(task_in, current_user.id)
    if not task:
        raise HTTPException(status_code=500, detail='Failed to create task')
    return task


@router.patch("/{task_id}", response_model=STaskOut)
async def patch_task(task_id: int, task_in: STaskIn, current_user: User = Depends(get_current_user)):
    task = await TaskService.update_task(task_id, task_in, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail='Task not found or update failed')
    return task


@router.patch("/{task_id}/toggle", response_model=STaskOut)
async def toggle_task(task_id: int, current_user: User = Depends(get_current_user)):
    task = await TaskDAO.find_one_or_none(id=task_id, owner_id=current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    new_status = not task.is_completed

    result = await TaskService.change_is_completed(task_id, new_status, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail='Toggle failed')
    return result


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, current_user: User = Depends(get_current_user)):
    deleted = await TaskDAO.delete(id=task_id, owner_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
    return None
