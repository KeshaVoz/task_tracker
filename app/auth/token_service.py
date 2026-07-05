import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Response, status
from app.config import settings
from app.redis_client import get_redis
from app.schemas.auth import STokenPayload
from app.exceptions.base import AppServiceException


class TokenService:
    @classmethod
    def _create_jwt(cls, user_id: int, ttl: timedelta, token_type: str) -> str:
        exp = datetime.now(timezone.utc) + ttl
        payload = STokenPayload(
            sub=user_id,
            type=token_type,
            exp=int(exp.timestamp()),
        ).model_dump()
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

    @classmethod
    def create_access_token(cls, user_id: int) -> str:
        return cls._create_jwt(user_id, timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN), "access")

    @classmethod
    def create_refresh_token(cls, user_id: int) -> str:
        return cls._create_jwt(user_id, timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS), "refresh")

    @staticmethod
    def decode_token(token: str, options: dict = None) -> STokenPayload:
        try:
            data = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG], options=options)
            return STokenPayload(**data)
        except jwt.ExpiredSignatureError:
            raise
        except (jwt.DecodeError, jwt.InvalidTokenError, Exception):
            raise AppServiceException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid or corrupted security session. Please log in again."
            )

    @staticmethod
    def _token_key(user_id: int, token: str) -> str:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return f"refresh:tasktracker:{user_id}:{token_hash}"

    @classmethod
    async def store_refresh_token_in_redis(cls, user_id: int, token: str) -> None:
        redis = await get_redis()
        key = cls._token_key(user_id, token)
        await redis.set(key, "1", ex=settings.REFRESH_TOKEN_TTL_DAYS * 24 * 3600)

    @classmethod
    async def is_refresh_token_in_redis_valid(cls, user_id: int, token: str) -> bool:
        redis = await get_redis()
        key = cls._token_key(user_id, token)
        value = await redis.get(key)
        return value is not None

    @classmethod
    async def delete_refresh_token_from_redis(cls, user_id: int, token: str) -> None:
        redis = await get_redis()
        key = cls._token_key(user_id, token)
        await redis.delete(key)

    @classmethod
    async def create_auth_response(cls, user_id: int) -> Response:
        access_token = cls.create_access_token(user_id)
        refresh_token = cls.create_refresh_token(user_id)
        
        await cls.store_refresh_token_in_redis(user_id, refresh_token)

        response = Response(status_code=status.HTTP_200_OK)       
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            max_age=settings.ACCESS_TOKEN_TTL_MIN * 60,
            samesite="lax"
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            max_age=settings.REFRESH_TOKEN_TTL_DAYS * 24 * 3600,
            samesite="lax"
        )        
        return response

    @classmethod
    def create_refresh_response(cls, user_id: int) -> Response:
        new_access_token = cls.create_access_token(user_id)
        response = Response(status_code=status.HTTP_200_OK)
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=False,
            max_age=settings.ACCESS_TOKEN_TTL_MIN * 60,
            samesite="lax"
        )
        return response