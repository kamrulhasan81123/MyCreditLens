import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id"), nullable=False)
    analyst_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    override_type: Mapped[str] = mapped_column(String(50), nullable=True)
    override_reason: Mapped[str] = mapped_column(Text, nullable=True)
    approved_amount: Mapped[float] = mapped_column(Float, nullable=True)
    approved_term_months: Mapped[int] = mapped_column(nullable=True)
    conditions: Mapped[dict] = mapped_column(JSON, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="decisions")
    analyst: Mapped["User"] = relationship("User", back_populates="decisions")