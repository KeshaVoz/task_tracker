from fastapi import Response
from fastapi.responses import JSONResponse
from app.auth.base import create_access_token
from app.config import settings
from app.services.auth import AuthService


async def create_auth_response(user_id: int, ttl_days: int = settings.REFRESH_TOKEN_TTL_DAYS) -> Response:
    print('create_auth_response')
    access_token, refresh_token = await AuthService.create_tokens(user_id)
    response = JSONResponse({'access_token': access_token})
    print(f'create_auth_response tk: {refresh_token}')        
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        max_age=ttl_days*24*3600,
        samesite='lax'
    )        
    return response


async def create_refresh_response(user_id: int,  ttl_days: int = settings.REFRESH_TOKEN_TTL_DAYS) -> Response:
    new_access_token = create_access_token(user_id)
    response = JSONResponse({'access_token': new_access_token})
    return response