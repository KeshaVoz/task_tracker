import logging
from fastapi import Request, status
from app.dao.users import UserDAO
from app.schemas.users import SUserOut
from app.exceptions.base import AppServiceException


logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> SUserOut:
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise AppServiceException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            message="Session expired. Please log in again."
        )

    user = await UserDAO.find_one_or_none(id=user_id)        
    if not user:
        raise AppServiceException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            message="User not found."
        )    
         
    return SUserOut.model_validate(user)