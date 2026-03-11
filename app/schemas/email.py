from pydantic import BaseModel
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