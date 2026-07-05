import logging
import jwt
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.auth.token_service import TokenService
from app.config import settings


logger = logging.getLogger(__name__)


class SilentRefreshMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")
        
        user_id = None
        should_refresh_access = False

        if access_token:
            try:
                payload = TokenService.decode_token(access_token)
                if payload.type == "access":
                    user_id = payload.sub
            except jwt.ExpiredSignatureError:
                should_refresh_access = True
            except Exception as e:
                logger.warning("Malformed access token: %s", e)

        if (not user_id or should_refresh_access) and refresh_token:
            try:
                payload = TokenService.decode_token(refresh_token)
                if payload.type == "refresh":
                    try:
                        is_valid = await TokenService.is_refresh_token_in_redis_valid(payload.sub, refresh_token)
                    except Exception as redis_error:
                        logger.error("Redis is unavailable during silent refresh: %s", redis_error, exc_info=True)
                        is_valid = False
                    
                    if is_valid:
                        user_id = payload.sub
                        should_refresh_access = True
                        
            except jwt.ExpiredSignatureError:
                logger.info("Refresh token expired. User must log in again.")
            except Exception as e:
                logger.error("Refresh token validation failed: %s", e)

        request.state.user_id = user_id
        response: Response = await call_next(request)

        if user_id and should_refresh_access and response.status_code < 400:
            new_access_token = TokenService.create_access_token(user_id)
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                httponly=True,
                secure=True,
                max_age=settings.ACCESS_TOKEN_TTL_MIN * 60,
                samesite="lax"
            )
            logger.info("Silent refresh successfully injected into response for user %s", user_id)

        return response