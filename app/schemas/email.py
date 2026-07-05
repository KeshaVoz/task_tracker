from pydantic import BaseModel, Field
from typing import List


class SEmailData(BaseModel):
    email: str
    subject: str  
    body: str


class SDailyReportData(BaseModel):
    total_pending: int
    pending_titles: List[str]
    completed_count: int
    completed_titles: List[str]


class SSummaryReportRequest(BaseModel):
    total_pending: int
    pending_titles: List[str] = Field(default_factory=list)
    completed_count: int
    completed_titles: List[str] = Field(default_factory=list)
    user_email: str
    target_date: str 
    user_id: int