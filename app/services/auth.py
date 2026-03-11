from app.dao.users import UserDAO
from app.models.users import User
from app.auth.base import hash_password, verify_password, create_access_token, create_refresh_token
from app.auth.refresh_store import store_refresh_token_in_redis
from app.schemas.users import SUserCreate, SUserOut
from app.tasks.email import send_welcome_email

class AuthService:
    @staticmethod
    async def register(email: str, password: str) -> User:
        existing = await UserDAO.find_one_or_none(email=email)
        if existing:
            raise ValueError('This email is already taken')
        
        hashed = hash_password(password)
        user_data = SUserCreate(email=email, hashed_password=hashed).model_dump()
        send_welcome_email.delay(email)
        print('after welcome task')
        return await UserDAO.add(**user_data)

    @staticmethod
    async def authenticate(email: str, password: str) -> User:
        user = await UserDAO.find_one_or_none(email=email)
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError('Invalid credentials')
        return SUserOut.model_validate(user)

    @staticmethod
    async def create_tokens(user_id: int):
        access = create_access_token(user_id)
        refresh = create_refresh_token(user_id)
        print('Auth create tokens')
        await store_refresh_token_in_redis(user_id, refresh)
        return access, refresh