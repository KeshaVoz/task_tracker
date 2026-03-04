from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Response, status
from app.schemas.users import SUserOut
from app.services.auth import AuthService
from app.auth.base import  decode_token
from app.auth.refresh_store import delete_refresh_token_from_redis, is_refresh_token_in_redis_valid
from app.dependencies import get_current_user
from app.utils.auth import create_auth_response, create_refresh_response


router = APIRouter(prefix="", tags=["auth"]) 


@router.post("/user")
async def register(email: str = Form(...), password: str = Form(...)):
    try:
        user = await AuthService.register(email, password)
        response = await create_auth_response(user.id)
        return response
            
    except ValueError as e:
        raise HTTPException(status_code=409, detail={'message': str(e)})


@router.get("/user", response_model=SUserOut)
async def get_current_user(user: SUserOut = Depends(get_current_user)):
    return user


@router.post("/session")
async def login(email: str = Form(...), password: str = Form(...)):
    user = await AuthService.authenticate(email, password)   
    response = await create_auth_response(user.id)
    return response


@router.delete("/session")
async def logout(response: Response, refresh_token: str = Cookie(None)):
    if refresh_token:
        try:
            payload = decode_token(refresh_token)  
            if payload.type != 'refresh':
                raise HTTPException(status_code=400, detail='Invalid token type')
            await delete_refresh_token_from_redis(payload.sub, refresh_token)
        
        except Exception:
            pass
    
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie('refresh_token')
    return response


@router.post("/session/refresh")
async def refresh_token(refresh_token: str = Cookie(None)):
    if not refresh_token:
        raise HTTPException(401, detail={'message': 'No refresh token'})
    
    payload = decode_token(refresh_token)
    if payload.type != 'refresh':
        raise HTTPException(401, detail={'message': 'Invalid token type'})
    
    if not await is_refresh_token_in_redis_valid(payload.sub, refresh_token):
        raise HTTPException(401, detail={'message': 'Invalid/expired refresh token'})

    response = await create_refresh_response(user_id=payload.sub)
    return response
