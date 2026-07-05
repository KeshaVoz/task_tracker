import logging
from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.auth.token_service import TokenService
from app.dependencies.auth import get_current_user
from app.schemas.users import SUserOut
from app.schemas.users import SUserRegister, SUserLogin
from app.services.auth import AuthService


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/user")
async def register(form_data: dict = Depends(SUserRegister.as_form)) -> Response:
    try:
        validated_data = SUserRegister(**form_data)
    except ValidationError as e:
        raise RequestValidationError(e.errors())
    
    user = await AuthService.register(validated_data.email, validated_data.password)
    return await TokenService.create_auth_response(user.id)


@router.get("/user", response_model=SUserOut)
async def get_user_profile(user: SUserOut = Depends(get_current_user)) -> SUserOut:
    return user


@router.post("/session")
async def login(form_data: dict = Depends(SUserLogin.as_form)) -> Response:
    try:
        validated_data = SUserLogin(**form_data)
    except ValidationError as e:
        raise RequestValidationError(e.errors())
        
    user = await AuthService.authenticate(validated_data.email, validated_data.password)   
    return await TokenService.create_auth_response(user.id)


@router.delete("/session")
async def logout(response: Response, refresh_token: str = Cookie(None)) -> Response:
    if refresh_token:
        try:
            payload = TokenService.decode_token(refresh_token, options={"verify_exp": False})  
            if payload.type == "refresh":
                await TokenService.delete_refresh_token_from_redis(payload.sub, refresh_token)
        except Exception as e:
            logger.warning("Failed to revoke token during logout: %s", e)
    
    response.status_code = status.HTTP_204_NO_CONTENT
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response