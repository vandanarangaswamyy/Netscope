import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from dbnode.main import app
from dbnode.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_override():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def override_settings(**kwargs):
    app.dependency_overrides[get_settings] = lambda: Settings(**kwargs)


def test_health_returns_node_identity():
    override_settings(NODE_ID="node-test", NODE_ROLE="analytics-worker")
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "node_id": "node-test",
        "role": "analytics-worker",
    }


def test_node_returns_latency_configuration():
    override_settings(NODE_ID="node-test", SIMULATED_LATENCY_MS=42)
    client = TestClient(app)

    response = client.get("/node")

    assert response.status_code == 200
    assert response.json()["simulated_latency_ms"] == 42


def test_query_includes_sql_and_elapsed_time():
    override_settings(NODE_ID="node-test", SIMULATED_LATENCY_MS=1)
    client = TestClient(app)

    response = client.get("/query", params={"sql": "select count(*) from fact_sales"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["node_id"] == "node-test"
    assert payload["status"] == "ok"
    assert payload["sql"] == "select count(*) from fact_sales"
    assert payload["elapsed_ms"] >= 1


def test_metrics_exposes_node_info():
    override_settings(NODE_ID="node-test", NODE_ROLE="analytics-worker")
    client = TestClient(app)

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert 'dbnode_info{node_id="node-test",role="analytics-worker"} 1.0' in response.text


def test_metrics_counts_application_requests():
    override_settings(NODE_ID="node-test")
    client = TestClient(app)

    health_response = client.get("/health")
    metrics_response = client.get("/metrics")

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200
    assert "dbnode_http_requests_total" in metrics_response.text
    assert 'dbnode_http_requests_total{method="GET",node_id="node-test",path="/health",status_code="200"}' in metrics_response.text


def test_rejects_negative_latency():
    with pytest.raises(ValidationError, match="SIMULATED_LATENCY_MS must be non-negative"):
        Settings(SIMULATED_LATENCY_MS=-1)
