"""End-to-end development seed.

Produces the full vertical slice so the local database demonstrates the whole
workflow instead of sitting at zero rows:

    Borrower -> Application -> Consent (incl. credit_scoring) -> Data source ->
    Transactions -> real model score (Prediction) -> SHAP Explanation ->
    Analyst Decision -> Audit logs.

Uses NO real borrower information. Idempotent: safe to run repeatedly.

Run (from backend/ with the project venv):
    .venv\\Scripts\\python -m app.scripts.seed_demo
"""

import asyncio
from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.database import async_session
from app.models.application import Application
from app.models.consent import Consent
from app.models.data_source import DataSource
from app.models.decision import Decision
from app.models.transaction import Transaction
from app.schemas.application import ApplicationCreate
from app.schemas.auth import UserCreate
from app.services.application_service import ApplicationService
from app.services.audit_service import add_audit_log
from app.services.auth_service import AuthService
from app.services.borrower_service import BorrowerService
from app.services.scoring_service import SCORING_CONSENT_TYPE, ScoringService

DEMO_USERS = [
    {"email": "admin@mycreditlens.com", "password": "DemoPass123!", "full_name": "Demo Admin", "role": "admin"},
    {"email": "analyst@mycreditlens.com", "password": "DemoPass123!", "full_name": "Demo Analyst", "role": "credit_analyst"},
    {"email": "compliance@mycreditlens.com", "password": "DemoPass123!", "full_name": "Demo Compliance Reviewer", "role": "compliance_reviewer"},
    {"email": "borrower@example.com", "password": "DemoPass123!", "full_name": "Demo Borrower", "role": "borrower"},
    {"email": "borrower2@example.com", "password": "DemoPass123!", "full_name": "Second Demo Borrower", "role": "borrower"},
]

# Two synthetic personas (NOT real people).
PERSONAS = [
    {
        "email": "borrower@example.com",
        "borrower": {
            "borrower_type": "gig_worker",
            "phone": "+60000000000",
            "date_of_birth": date(1990, 5, 1),
            "employment_type": "gig",
            "monthly_income_declared": 4500.0,
            "employment_duration_years": 4.0,
            "home_ownership": "RENT",
        },
        "application": {"purpose": "Working capital for delivery work", "loan_intent": "VENTURE", "requested_amount": 5000.0, "requested_term_months": 12},
    },
    {
        "email": "borrower2@example.com",
        "borrower": {
            "borrower_type": "individual",
            "phone": "+60111111111",
            "date_of_birth": date(1985, 9, 15),
            "employment_type": "full_time",
            "monthly_income_declared": 9000.0,
            "employment_duration_years": 8.0,
            "home_ownership": "MORTGAGE",
        },
        "application": {"purpose": "Home improvement", "loan_intent": "HOMEIMPROVEMENT", "requested_amount": 20000.0, "requested_term_months": 36},
    },
]


async def _ensure_consent(db, application_id: str, source_type: str) -> None:
    existing = (
        await db.execute(
            select(Consent).where(Consent.application_id == application_id, Consent.data_source_type == source_type)
        )
    ).scalar_one_or_none()
    if existing:
        if not existing.granted:
            existing.granted = True
            existing.granted_at = datetime.utcnow()
        return
    db.add(
        Consent(
            application_id=application_id,
            data_source_type=source_type,
            granted=True,
            granted_at=datetime.utcnow(),
            consent_version="v1",
        )
    )


async def _ensure_transactions(db, application_id: str, monthly_income: float) -> None:
    existing = (
        await db.execute(select(DataSource).where(DataSource.application_id == application_id))
    ).scalar_one_or_none()
    if existing:
        return
    source = DataSource(
        application_id=application_id,
        source_type="bank_statement",
        file_name="demo_statement.csv",
        storage_bucket="local",
        validation_status="validated",
        reliability_score=0.9,
        missing_rate=0.0,
        record_count=6,
    )
    db.add(source)
    await db.flush()
    start = date.today() - timedelta(days=150)
    for i in range(6):
        db.add(
            Transaction(
                data_source_id=source.id,
                transaction_date=start + timedelta(days=30 * i),
                description=f"Salary/income month {i + 1}",
                amount=monthly_income,
                direction="credit",
                category="income",
            )
        )
        db.add(
            Transaction(
                data_source_id=source.id,
                transaction_date=start + timedelta(days=30 * i + 5),
                description=f"Living expenses month {i + 1}",
                amount=-monthly_income * 0.6,
                direction="debit",
                category="expense",
            )
        )


async def _seed_persona(db, users: dict, persona: dict) -> None:
    user = users[persona["email"]]
    borrower_service = BorrowerService(db)
    borrower = await borrower_service.get_by_user_id(user.id)
    for key, value in persona["borrower"].items():
        setattr(borrower, key, value)
    await db.commit()

    application_service = ApplicationService(db)
    existing = await application_service.list_for_user(user, 1, 1)
    if existing["total"] == 0:
        await application_service.create(user, ApplicationCreate(**persona["application"]))
    application = (
        await db.execute(select(Application).where(Application.borrower_id == borrower.id))
    ).scalars().first()

    await _ensure_consent(db, application.id, "bank_statement")
    await _ensure_consent(db, application.id, SCORING_CONSENT_TYPE)
    await _ensure_transactions(db, application.id, persona["borrower"]["monthly_income_declared"])
    if application.status == "draft":
        application.status = "submitted"
        application.submitted_at = datetime.utcnow()
    await db.commit()

    # Real model score through the production scoring path.
    scoring = ScoringService(db)
    prediction = await scoring.score_application(application.id)

    # Analyst decision on the scored application.
    existing_decision = (
        await db.execute(select(Decision).where(Decision.application_id == application.id))
    ).scalar_one_or_none()
    if not existing_decision:
        analyst = users["analyst@mycreditlens.com"]
        decision_value = "approved" if prediction.risk_band == "low" else "manual_review"
        decision = Decision(
            application_id=application.id,
            analyst_id=analyst.id,
            decision=decision_value,
            reason=f"Auto-seeded analyst decision based on {prediction.risk_band} risk band.",
            approved_amount=persona["application"]["requested_amount"] if decision_value == "approved" else None,
            approved_term_months=persona["application"]["requested_term_months"] if decision_value == "approved" else None,
        )
        db.add(decision)
        await db.flush()
        application.status = decision_value
        application.decided_at = datetime.utcnow()
        add_audit_log(
            db,
            user_id=analyst.id,
            action="decision.created",
            resource_type="decision",
            resource_id=decision.id,
            details={"application_id": application.id, "decision": decision_value},
        )
        await db.commit()

    print(
        f"  {persona['email']}: application {application.reference} scored "
        f"PD={prediction.probability_of_default:.4f} band={prediction.risk_band} "
        f"model_version={prediction.model_version}"
    )


async def main() -> None:
    async with async_session() as db:
        auth = AuthService(db)
        users = {}
        for payload in DEMO_USERS:
            try:
                user = await auth.register(UserCreate(**payload), allow_privileged=True)
            except Exception:
                user = await auth._get_user_by_email(payload["email"])
            users[payload["email"]] = user

        for persona in PERSONAS:
            await _seed_persona(db, users, persona)

    print("Demo seed completed.")


if __name__ == "__main__":
    asyncio.run(main())
