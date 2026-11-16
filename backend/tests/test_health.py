from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    # Root serves the SPA frontend or JSON if not built
    assert "<!doctype html>" in response.text or "EvidenceRAG API" in response.text

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
