from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class STaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class STaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None


class STaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    owner_id: int
    
    class Config:
        from_attributes = True


class STasksList(BaseModel):
    tasks: List[STaskOut]