from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime


class DecisionCreate(BaseModel):
    application_id: Optional[str] = None
    decision: Literal["approved", "rejected", "manual_review", "information_requested"]
    reason: str
    override_type: Optional[str] = None
    override_reason: Optional[str] = None
    approved_amount: Optional[float] = None
    approved_term_months: Optional[int] = None
    conditions: Optional[dict] = None


class DecisionOut(BaseModel):
    id: str
    application_id: str
    analyst_id: Optional[str]
    decision: str
    reason: Optional[str]
    override_type: Optional[str]
    override_reason: Optional[str]
    approved_amount: Optional[float]
    approved_term_months: Optional[int]
    conditions: Optional[dict]
    decided_at: datetime

    class Config:
        from_attributes = True
