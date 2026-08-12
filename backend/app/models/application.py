import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class ApplicationStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    DATA_PENDING = "data_pending"
    READY_FOR_SCORING = "ready_for_scoring"
    SCORED = "scored"
    MANUAL_REVIEW = "manual_review"
    INFORMATION_REQUESTED = "information_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPEALED = "appealed"


class RiskBand(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LoanIntent(str, enum.Enum):
    """Loan purpose. Levels match the application-PD model's `loan_intent`
    feature (see ml.datasets.application_pd)."""

    PERSONAL = "PERSONAL"
    EDUCATION = "EDUCATION"
    MEDICAL = "MEDICAL"
    VENTURE = "VENTURE"
    HOMEIMPROVEMENT = "HOMEIMPROVEMENT"
    DEBTCONSOLIDATION = "DEBTCONSOLIDATION"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    borrower_id: Mapped[str] = mapped_column(String(36), ForeignKey("borrowers.id"), nullable=False)
    purpose: Mapped[str] = mapped_column(String(500), nullable=False)
    # Structured loan purpose required by the application-PD model. `purpose`
    # remains as free-text human context.
    loan_intent: Mapped[LoanIntent] = mapped_column(
        SAEnum(LoanIntent, values_callable=lambda enum_class: [item.value for item in enum_class]),
        nullable=True,
    )
    requested_amount: Mapped[float] = mapped_column(Float, nullable=False)
    requested_term_months: Mapped[int] = mapped_column(nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, values_callable=lambda enum_class: [item.value for item in enum_class]),
        nullable=False,
        default=ApplicationStatus.DRAFT,
    )
    risk_band: Mapped[RiskBand] = mapped_column(
        SAEnum(RiskBand, values_callable=lambda enum_class: [item.value for item in enum_class]),
        nullable=True,
    )
    probability_of_default: Mapped[float] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=True)
    recommended_action: Mapped[str] = mapped_column(String(50), nullable=True)
    data_quality_score: Mapped[float] = mapped_column(Float, nullable=True)
    assigned_analyst_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    borrower: Mapped["Borrower"] = relationship("Borrower", back_populates="applications")
    consents: Mapped[list["Consent"]] = relationship("Consent", back_populates="application")
    data_sources: Mapped[list["DataSource"]] = relationship("DataSource", back_populates="application")
    predictions: Mapped[list["Prediction"]] = relationship("Prediction", back_populates="application")
    explanations: Mapped[list["Explanation"]] = relationship("Explanation", back_populates="application")
    policy_results: Mapped[list["PolicyResult"]] = relationship("PolicyResult", back_populates="application")
    decisions: Mapped[list["Decision"]] = relationship("Decision", back_populates="application")
    appeals: Mapped[list["Appeal"]] = relationship("Appeal", back_populates="application")
    integrity_alerts: Mapped[list["IntegrityAlert"]] = relationship("IntegrityAlert", back_populates="application")
    features: Mapped[list["EngineeredFeature"]] = relationship("EngineeredFeature", back_populates="application")
