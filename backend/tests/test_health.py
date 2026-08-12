from fastapi.testclient import TestClient

from app.main import app


def test_process_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_model_health_reports_demo_when_artifacts_missing():
    client = TestClient(app)
    response = client.get("/health/model")
    assert response.status_code == 200
    assert response.json()["status"] in {"ready", "demo_mode"}
