import logging
from fastapi import status
from app.dao.users import UserDAO
from app.auth.base import hash_password, verify_password
from app.schemas.users import SUserCreate, SUserOut
from app.exceptions.base import AppServiceException


logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    async def register(email: str, password: str) -> SUserOut:
        existing = await UserDAO.find_one_or_none(email=email)
        if existing:
            logger.warning("Registration failed: Email %s is already taken", email)
            raise AppServiceException(
                status_code=status.HTTP_409_CONFLICT,
                message="This email is already taken"
            )
        
        hashed = hash_password(password)
        user_data = SUserCreate(email=email, hashed_password=hashed).model_dump()
        
        new_user = await UserDAO.add(**user_data)

        from app.tasks.email import send_welcome_email
        send_welcome_email.delay(email)
        logger.info("Welcome email tasked triggered for %s after DB persist", email)
        
        return SUserOut.model_validate(new_user)

    @staticmethod
    async def authenticate(email: str, password: str) -> SUserOut:
        user = await UserDAO.find_one_or_none(email=email)
        if not user or not verify_password(password, user.hashed_password):
            logger.warning("Authentication failed for email: %s", email)
            raise AppServiceException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid credentials"
            )
            
        return SUserOut.model_validate(user)

