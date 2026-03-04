from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class STaskIn(BaseModel):
    title: str
    description: Optional[str] = None


class STaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    is_completed: bool
    updated_at: datetime
    
    class Config:
        from_attributes = True


class STasksList(BaseModel):
    tasks: List[STaskOut]