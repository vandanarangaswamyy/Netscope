import httpx
import pytest
from fastapi.testclient import TestClient

from trafficgen.main import TrafficWorker, app, query_url
from trafficgen.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_override():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def override_settings(**kwargs):
    app.dependency_overrides[get_settings] = lambda: Settings(**kwargs)


def test_query_url_adds_encoded_sql_parameter():
    settings = Settings(TARGET_BASE_URL="http://nginx:8080/")

    assert query_url(settings, 7) == "http://nginx:8080/query?sql=select+7"


def test_health_reports_config_without_running_worker():
    override_settings(TRAFFIC_ENABLED=False, TARGET_BASE_URL="http://nginx:8080", REQUESTS_PER_SECOND=3)
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["target_base_url"] == "http://nginx:8080"
    assert response.json()["traffic_enabled"] is False
    assert response.json()["requests_per_second"] == 3


@pytest.mark.anyio
async def test_worker_records_successful_request():
    settings = Settings(TARGET_BASE_URL="http://example.test", SLO_LATENCY_MS=1000)
    worker = TrafficWorker(settings)

    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://example.test/query?sql=select+1"
        return httpx.Response(200, json={"status": "ok"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await worker.send_once(client)

    assert worker.sent == 1
    assert worker.successes == 1
    assert worker.failures == 0
    assert worker.last_error is None


@pytest.mark.anyio
async def test_worker_records_network_error():
    settings = Settings(TARGET_BASE_URL="http://example.test")
    worker = TrafficWorker(settings)

    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await worker.send_once(client)

    assert worker.sent == 1
    assert worker.successes == 0
    assert worker.failures == 1
    assert "connection refused" in worker.last_error
