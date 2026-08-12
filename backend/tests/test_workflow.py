import asyncio

from app.schemas.auth import UserCreate
from app.services.auth_service import AuthService


def register_borrower(client, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "DemoPass123!",
            "full_name": "Test Borrower",
            "role": "borrower",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def create_staff(client, role: str, email: str) -> dict:
    async def create() -> None:
        async with client.session_factory() as session:
            await AuthService(session).register(
                UserCreate(
                    email=email,
                    password="DemoPass123!",
                    full_name="Test Staff",
                    role=role,
                ),
                allow_privileged=True,
            )

    asyncio.run(create())
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "DemoPass123!"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_registration_rejects_privileged_self_service(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "password": "DemoPass123!",
            "full_name": "Fake Admin",
            "role": "admin",
        },
    )
    assert response.status_code == 403


def test_borrower_workflow_enforces_ownership_and_staff_decision(client):
    borrower = register_borrower(client, "borrower-one@example.com")
    other_borrower = register_borrower(client, "borrower-two@example.com")

    create_response = client.post(
        "/api/v1/applications/",
        headers=auth_header(borrower),
        json={"purpose": "Working capital", "requested_amount": 5000, "requested_term_months": 12},
    )
    assert create_response.status_code == 201, create_response.text
    application = create_response.json()

    denied = client.get(
        f"/api/v1/applications/{application['id']}",
        headers=auth_header(other_borrower),
    )
    assert denied.status_code == 404

    consent = client.post(
        f"/api/v1/applications/{application['id']}/consents",
        headers=auth_header(borrower),
        json={"data_source_type": "bank_statement"},
    )
    assert consent.status_code == 201, consent.text
    assert consent.json()["granted"] is True

    submitted = client.post(
        f"/api/v1/applications/{application['id']}/submit",
        headers=auth_header(borrower),
    )
    assert submitted.status_code == 200, submitted.text

    analyst = create_staff(client, "credit_analyst", "analyst@example.com")
    decision = client.post(
        f"/api/v1/applications/{application['id']}/decisions",
        headers=auth_header(analyst),
        json={"decision": "approved", "reason": "Verified repayment capacity"},
    )
    assert decision.status_code == 201, decision.text
    assert decision.json()["decision"] == "approved"

    visible = client.get(
        f"/api/v1/applications/{application['id']}/decisions",
        headers=auth_header(borrower),
    )
    assert visible.status_code == 200
    assert len(visible.json()) == 1
