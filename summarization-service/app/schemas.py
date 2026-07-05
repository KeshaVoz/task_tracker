from pydantic import BaseModel, Field
from typing import List


class SSummaryReportRequest(BaseModel):
    total_pending: int
    pending_titles: List[str] = Field(default_factory=list)
    completed_count: int
    completed_titles: List[str] = Field(default_factory=list)
    user_email: str
    target_date: str
    user_id: int


class SSummaryReportResponse(BaseModel):
    report_text: str
    correlation_id: str
    user_email: str
    target_date: str
    user_id: int


class SClearCacheCommand(BaseModel):
    retention_days: int