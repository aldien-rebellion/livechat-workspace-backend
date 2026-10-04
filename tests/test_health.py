from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_health_check():
    response = client.get("/api/v1/healthcheck")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "livechat-workspace-backend"


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "livechat_active_websocket_connections" in response.text
    assert "livechat_messages_published_total" in response.text
    assert "livechat_messages_read_total" in response.text


# ---------------------------------------------------------------------------
# Workshop 12 – Cloud deployment health probe
# ---------------------------------------------------------------------------
def test_health_endpoint():
    """GET /health must return 200 with the cloud smoke-test payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["message"] == "Hello Sakon Nakhon Cloud!"
