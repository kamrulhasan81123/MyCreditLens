from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class DataSourceOut(BaseModel):
    id: str
    application_id: str
    source_type: str
    file_name: Optional[str]
    storage_bucket: Optional[str] = None
    storage_path: Optional[str] = None
    file_hash: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    validation_status: str
    reliability_score: Optional[float]
    missing_rate: Optional[float]
    date_coverage_start: Optional[date]
    date_coverage_end: Optional[date]
    record_count: Optional[int]
    issues: Optional[str]
    warnings: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DataSourceUploadResponse(BaseModel):
    id: str
    file_name: str
    source_type: str
    validation_status: str
    record_count: Optional[int]
    issues: Optional[str]
    warnings: Optional[str]
    reliability_score: Optional[float] = None
