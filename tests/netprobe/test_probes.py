import socket

import httpx
import pytest

from netprobe.probes import (
    check_http_health,
    check_rejected_traffic,
    check_route,
    check_tcp,
    parse_target,
    sample_latency,
)


def test_parse_target_defaults_http_port():
    assert parse_target("localhost:8080") == ("localhost", 8080, "http://localhost:8080")


def test_parse_target_defaults_https_port():
    assert parse_target("https://example.com") == ("example.com", 443, "https://example.com")


def test_check_tcp_success():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    host, port = server.getsockname()

    try:
        result = check_tcp(host, port, timeout_seconds=1)
    finally:
        server.close()

    assert result.status == "ok"
    assert result.details["elapsed_ms"] >= 0


def test_check_http_health_success(monkeypatch):
    def fake_get(url, timeout):
        assert url == "http://localhost:8080/health"
        assert timeout == 2
        return httpx.Response(200, json={"status": "healthy"})

    monkeypatch.setattr(httpx, "get", fake_get)

    result = check_http_health("http://localhost:8080", timeout_seconds=2)

    assert result.status == "ok"
    assert result.details["status_code"] == 200


def test_sample_latency_fails_on_http_error(monkeypatch):
    def fake_get(url, params, timeout):
        return httpx.Response(503, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    result = sample_latency("http://localhost:8080", samples=1, timeout_seconds=2)

    assert result.status == "fail"
    assert result.details["completed_samples"] == 0


def test_check_route_reports_unknown_when_route_tool_missing(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("subprocess.run", fake_run)

    result = check_route("localhost", timeout_seconds=1)

    assert result.status == "unknown"


def test_check_rejected_traffic_ok(monkeypatch):
    def fake_get(url, params, timeout):
        assert url == "http://prometheus:9090/api/v1/query"
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            json={"status": "success", "data": {"result": [{"value": [1, "0"]}]}},
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = check_rejected_traffic("http://prometheus:9090", timeout_seconds=2)

    assert result.status == "ok"
    assert result.details["rejected_requests"] == 0


def test_check_rejected_traffic_fails_when_rejections_present(monkeypatch):
    def fake_get(url, params, timeout):
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            json={"status": "success", "data": {"result": [{"value": [1, "3"]}]}},
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = check_rejected_traffic("http://prometheus:9090", timeout_seconds=2)

    assert result.status == "fail"
    assert result.details["rejected_requests"] == 3
