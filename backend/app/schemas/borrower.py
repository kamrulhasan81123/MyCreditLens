from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class BorrowerCreate(BaseModel):
    borrower_type: str
    national_id: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    employment_type: Optional[str] = None
    employer_name: Optional[str] = None
    monthly_income_declared: Optional[float] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    years_in_business: Optional[float] = None
    # Inputs required by the application-PD model.
    home_ownership: Optional[str] = None
    employment_duration_years: Optional[float] = None


class BorrowerUpdate(BaseModel):
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    employment_type: Optional[str] = None
    employer_name: Optional[str] = None
    monthly_income_declared: Optional[float] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    years_in_business: Optional[float] = None
    home_ownership: Optional[str] = None
    employment_duration_years: Optional[float] = None


class BorrowerOut(BaseModel):
    id: str
    user_id: str
    borrower_type: str
    national_id: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    date_of_birth: Optional[date]
    employment_type: Optional[str]
    employer_name: Optional[str]
    monthly_income_declared: Optional[float]
    business_name: Optional[str]
    business_type: Optional[str]
    years_in_business: Optional[float]
    home_ownership: Optional[str] = None
    employment_duration_years: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BorrowerListOut(BaseModel):
    items: list[BorrowerOut]
    total: int
    page: int
    page_size: int
    total_pages: int
