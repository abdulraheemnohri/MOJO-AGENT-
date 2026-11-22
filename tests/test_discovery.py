from fastapi.testclient import TestClient
from mojo_agent.api import app, _discover_ipv4_addresses

def test_discovery_endpoint_reports_service_contract():
    response = TestClient(app).get("/api/v1/discovery")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "MOJO AGENT"
    assert payload["port"] == 8766
    assert payload["api_prefix"] == "/api/v1"
    assert payload["health_path"] == "/api/v1/health"
    assert isinstance(payload["addresses"], list)
    assert all(not address.startswith("127.") for address in payload["addresses"])

def test_discovery_helper_returns_unique_non_loopback_addresses():
    addresses = _discover_ipv4_addresses()
    assert len(addresses) == len(set(addresses))
    assert all(isinstance(address, str) and address for address in addresses)

def test_frontend_development_origin_cors_preflight():
    response = TestClient(app).options(
        "/api/v1/health",
        headers={"Origin":"http://localhost:5173","Access-Control-Request-Method":"GET"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
