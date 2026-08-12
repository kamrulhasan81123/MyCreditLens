from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExplanationOut(BaseModel):
    id: str
    application_id: str
    prediction_id: str
    method: str
    shap_values: Optional[dict]
    top_positive_factors: Optional[dict]
    top_negative_factors: Optional[dict]
    plain_language_explanation: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True


class ExplanationRequest(BaseModel):
    application_id: str
    method: str = "shap"