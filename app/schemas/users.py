from typing import List
from pydantic import BaseModel, EmailStr
from app.schemas.tasks import STaskOut


class SUserCreate(BaseModel):
    email: EmailStr
    hashed_password: str


class SUserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    tasks: List[STaskOut] = []

    class Config:
        from_attributes = True