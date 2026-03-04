from fastapi import HTTPException, Header
import jwt
from app.dao.users import UserDAO
from app.auth.base import decode_token
from app.schemas.users import SUserOut



async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith('Bearer'):
        raise HTTPException(401, 'Invalid auth header')
    
    token = authorization.split(' ')[1]    
    try:
        payload = decode_token(token)        
        user = await UserDAO.find_one_or_none(id=payload.sub)        
        if not user:
            raise HTTPException(401, 'User not found')            
        return SUserOut.model_validate(user)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, 'Token expired')
    except Exception as e:
        raise HTTPException(401, 'Invalid token')