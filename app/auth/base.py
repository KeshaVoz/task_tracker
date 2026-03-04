import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from app.config import settings
from app.schemas.auth import STokenPayload


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def _create_jwt(user_id: int, ttl: timedelta, token_type: str) -> str:
    exp = datetime.now(timezone.utc) + ttl
    payload = STokenPayload(
        sub=user_id,
        type=token_type,
        exp=int(exp.timestamp()),
    ).model_dump()
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def create_access_token(user_id: int) -> str:
    return _create_jwt(user_id, timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN), 'access')


def create_refresh_token(user_id: int) -> str:
    return _create_jwt(user_id, timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS), 'refresh')


def decode_token(token: str) -> STokenPayload:
    data = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    return STokenPayload(**data)
