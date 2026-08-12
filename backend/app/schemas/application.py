from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApplicationCreate(BaseModel):
    purpose: str
    requested_amount: float
    requested_term_months: Optional[int] = None
    loan_intent: Optional[str] = None


class ApplicationUpdate(BaseModel):
    purpose: Optional[str] = None
    requested_amount: Optional[float] = None
    requested_term_months: Optional[int] = None
    loan_intent: Optional[str] = None


class ApplicationOut(BaseModel):
    id: str
    reference: str
    borrower_id: str
    purpose: str
    loan_intent: Optional[str] = None
    requested_amount: float
    requested_term_months: Optional[int]
    status: str
    risk_band: Optional[str]
    probability_of_default: Optional[float]
    confidence: Optional[float]
    model_version: Optional[str]
    recommended_action: Optional[str]
    data_quality_score: Optional[float]
    assigned_analyst_id: Optional[str]
    submitted_at: Optional[datetime]
    scored_at: Optional[datetime]
    decided_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationListOut(BaseModel):
    items: list[ApplicationOut]
    total: int
    page: int
    page_size: int
    total_pages: int = 0
