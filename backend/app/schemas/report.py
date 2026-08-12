from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportCreate(BaseModel):
    application_id: Optional[str] = None
    report_type: str
    title: Optional[str] = None
    content: Optional[dict] = None
    summary: Optional[str] = None


class ReportOut(BaseModel):
    id: str
    application_id: str
    report_type: str
    title: Optional[str]
    content: Optional[dict]
    summary: Optional[str]
    generated_by: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True


class ReportGenerateRequest(BaseModel):
    report_type: str
    parameters: Optional[dict] = None
