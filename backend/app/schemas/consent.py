from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ConsentCreate(BaseModel):
    data_source_type: str


class ConsentUpdate(BaseModel):
    granted: Optional[bool] = None


class ConsentOut(BaseModel):
    id: str
    application_id: str
    data_source_type: str
    granted: bool
    granted_at: Optional[datetime]
    revoked_at: Optional[datetime]
    consent_version: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True