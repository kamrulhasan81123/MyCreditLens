from datetime import date, datetime

from pydantic import BaseModel


class TransactionOut(BaseModel):
    id: str
    data_source_id: str
    transaction_date: date
    description: str | None
    amount: float
    currency: str
    direction: str | None
    category: str | None
    is_anomaly: bool
    is_excluded: bool
    created_at: datetime

    class Config:
        from_attributes = True
