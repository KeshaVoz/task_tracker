from fastapi import APIRouter, Depends, Form,Response, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.models.users import User
from app.schemas.tasks import STaskOut, STaskIn, STaskUpdate
from app.dependencies.auth import get_current_user
from app.dao.tasks import TaskDAO
from app.services.tasks import TaskService


router = APIRouter(prefix="/task", tags=["tasks"])


@router.get("", response_model=list[STaskOut])
async def get_tasks(current_user: User = Depends(get_current_user)) -> list[STaskOut]:
    tasks = await TaskDAO.find_all(owner_id=current_user.id)
    return tasks


@router.post("", response_model=STaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    form_data: dict = Depends(STaskIn.as_form), 
    current_user: User = Depends(get_current_user)
) -> STaskOut:
    try:
        validated_data = STaskIn(**form_data)
    except ValidationError as e:
        raise RequestValidationError(e.errors())
        
    task = await TaskService.create_task(validated_data, current_user.id)
    return task


@router.patch("", response_model=STaskOut)
async def patch_task(
    id: int = Form(...),
    form_data: dict = Depends(STaskUpdate.as_form), 
    current_user: User = Depends(get_current_user)
) -> STaskOut:
    try:
        validated_data = STaskUpdate(**form_data)
    except ValidationError as e:
        raise RequestValidationError(e.errors())
        
    task = await TaskService.update_task(id, validated_data, current_user.id)
    return task


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    response: Response,                     
    id: int = Form(...),                    
    current_user: User = Depends(get_current_user)
) -> Response:
    await TaskService.delete_task(id, current_user.id)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


