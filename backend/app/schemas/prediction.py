from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PredictionOut(BaseModel):
    id: str
    application_id: str
    model_id: str
    probability_of_default: float
    raw_probability: Optional[float] = None
    calibrated_probability: Optional[float] = None
    risk_band: str
    confidence: Optional[float]
    uncertainty: Optional[float] = None
    is_ood: bool
    ood_score: Optional[float]
    calibration_status: Optional[str]
    scoring_mode: Optional[str] = None
    model_version: Optional[str] = None
    feature_schema_version: Optional[str] = None
    scored_at: datetime

    class Config:
        from_attributes = True


class ScoreRequest(BaseModel):
    application_id: str
    model_version: Optional[str] = None


class ScoreResponse(BaseModel):
    prediction_id: str
    application_id: str
    probability_of_default: float
    calibrated_probability: Optional[float] = None
    raw_probability: Optional[float] = None
    risk_band: str
    confidence: Optional[float] = None
    uncertainty: Optional[float] = None
    # Model identity: model_id is the DB UUID; model_version is the real,
    # human-readable version string (NOT the UUID).
    model_id: str
    model_version: str
    model_name: Optional[str] = None
    feature_schema_version: Optional[str] = None
    feature_version: Optional[str] = None
    scoring_mode: Optional[str] = None
    is_ood: bool
    ood_score: Optional[float] = None
    explanation_available: bool = False
    scored_at: datetime