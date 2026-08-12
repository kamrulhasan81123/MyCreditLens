import uuid
from datetime import datetime, date
from sqlalchemy import String, Float, Integer, Date, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    storage_bucket: Mapped[str] = mapped_column(String(100), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=True)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(20), default="pending")
    reliability_score: Mapped[float] = mapped_column(Float, nullable=True)
    missing_rate: Mapped[float] = mapped_column(Float, nullable=True)
    date_coverage_start: Mapped[date] = mapped_column(Date, nullable=True)
    date_coverage_end: Mapped[date] = mapped_column(Date, nullable=True)
    record_count: Mapped[int] = mapped_column(Integer, nullable=True)
    issues: Mapped[str] = mapped_column(Text, nullable=True)
    warnings: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="data_sources")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="data_source")
