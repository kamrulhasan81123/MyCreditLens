import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Explanation(Base):
    __tablename__ = "explanations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id"), nullable=False)
    prediction_id: Mapped[str] = mapped_column(String(36), ForeignKey("predictions.id"), nullable=False)
    method: Mapped[str] = mapped_column(String(50), default="shap")
    shap_values: Mapped[dict] = mapped_column(JSON, nullable=True)
    top_positive_factors: Mapped[dict] = mapped_column(JSON, nullable=True)
    top_negative_factors: Mapped[dict] = mapped_column(JSON, nullable=True)
    plain_language_explanation: Mapped[str] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="explanations")