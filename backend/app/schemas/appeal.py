from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime


class AppealCreate(BaseModel):
    application_id: Optional[str] = None
    reason: str
    evidence: Optional[dict] = None


class AppealUpdate(BaseModel):
    status: Literal["under_review", "resolved", "rejected"]
    reviewer_notes: Optional[str] = None
    resolution: Optional[str] = None


class AppealOut(BaseModel):
    id: str
    application_id: str
    reason: str
    evidence: Optional[dict]
    status: str
    reviewer_id: Optional[str]
    reviewer_notes: Optional[str]
    resolution: Optional[str]
    submitted_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True
