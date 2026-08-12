from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: str
    user_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict | None
    created_at: datetime

    class Config:
        from_attributes = True
