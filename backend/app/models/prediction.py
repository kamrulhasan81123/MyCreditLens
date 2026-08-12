import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id"), nullable=False)
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("ml_models.id"), nullable=False)
    probability_of_default: Mapped[float] = mapped_column(Float, nullable=False)
    # Raw (uncalibrated) vs calibrated probability, persisted separately (§7).
    raw_probability: Mapped[float] = mapped_column(Float, nullable=True)
    calibrated_probability: Mapped[float] = mapped_column(Float, nullable=True)
    risk_band: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    uncertainty: Mapped[float] = mapped_column(Float, nullable=True)
    is_ood: Mapped[bool] = mapped_column(Boolean, default=False)
    ood_score: Mapped[float] = mapped_column(Float, nullable=True)
    calibration_status: Mapped[str] = mapped_column(String(20), nullable=True)
    scoring_mode: Mapped[str] = mapped_column(String(30), nullable=True)
    # Denormalised, human-readable model + feature-schema versions so a
    # prediction remains auditable even if the ml_models row changes.
    model_version: Mapped[str] = mapped_column(String(50), nullable=True)
    feature_schema_version: Mapped[str] = mapped_column(String(50), nullable=True)
    feature_values: Mapped[dict] = mapped_column(JSON, nullable=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="predictions")
    model: Mapped["MLModel"] = relationship("MLModel", back_populates="predictions")