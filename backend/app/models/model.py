import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MLModel(Base):
    __tablename__ = "ml_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False)
    model_path: Mapped[str] = mapped_column(String(500), nullable=True)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=True)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=True)
    feature_names: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    trained_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    predictions: Mapped[list["Prediction"]] = relationship("Prediction", back_populates="model")
