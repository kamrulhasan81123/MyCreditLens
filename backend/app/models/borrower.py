import uuid
from datetime import datetime, date
from sqlalchemy import String, Float, Date, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class BorrowerType(str, enum.Enum):
    INDIVIDUAL = "individual"
    SOLE_PROPRIETOR = "sole_proprietor"
    MICRO_BUSINESS = "micro_business"
    GIG_WORKER = "gig_worker"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    SELF_EMPLOYED = "self_employed"
    GIG = "gig"
    UNEMPLOYED = "unemployed"


class HomeOwnership(str, enum.Enum):
    """Residential status. Levels match the application-PD model's
    `home_ownership` feature (see ml.datasets.application_pd)."""

    RENT = "RENT"
    OWN = "OWN"
    MORTGAGE = "MORTGAGE"
    OTHER = "OTHER"


class Borrower(Base):
    __tablename__ = "borrowers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    borrower_type: Mapped[BorrowerType] = mapped_column(
        SAEnum(BorrowerType, values_callable=lambda enum_class: [item.value for item in enum_class]),
        nullable=False,
    )
    national_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=True)
    employment_type: Mapped[EmploymentType] = mapped_column(
        SAEnum(EmploymentType, values_callable=lambda enum_class: [item.value for item in enum_class]),
        nullable=True,
    )
    employer_name: Mapped[str] = mapped_column(String(255), nullable=True)
    monthly_income_declared: Mapped[float] = mapped_column(Float, nullable=True)
    # Required inputs for the application-PD model (see ApplicationToModelAdapter).
    home_ownership: Mapped[HomeOwnership] = mapped_column(
        SAEnum(HomeOwnership, values_callable=lambda enum_class: [item.value for item in enum_class]),
        nullable=True,
    )
    employment_duration_years: Mapped[float] = mapped_column(Float, nullable=True)
    business_name: Mapped[str] = mapped_column(String(255), nullable=True)
    business_type: Mapped[str] = mapped_column(String(100), nullable=True)
    years_in_business: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="borrower_profile")
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="borrower")
