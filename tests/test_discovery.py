from fastapi.testclient import TestClient
from mojo_agent.api import app

def test_discovery_endpoint_reports_service_contract():
    response = TestClient(app).get("/api/v1/discovery")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "MOJO AGENT"
    assert payload["port"] == 8766
    assert payload["api_prefix"] == "/api/v1"
    assert payload["health_path"] == "/api/v1/health"

def test_frontend_development_origin_cors_preflight():
    response = TestClient(app).options(
        "/api/v1/health",
        headers={"Origin":"http://localhost:5173","Access-Control-Request-Method":"GET"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
