from pydantic import BaseModel


class STokenPayload(BaseModel):
    sub: int        
    type: str         
    exp: int

