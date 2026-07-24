from __future__ import annotations

import socket
import subprocess
from dataclasses import dataclass
from statistics import mean
from time import perf_counter
from urllib.parse import urljoin, urlparse

import httpx


@dataclass(frozen=True)
class ProbeResult:
    name: str
    status: str
    message: str
    details: dict[str, object]


def ok(name: str, message: str, **details: object) -> ProbeResult:
    return ProbeResult(name=name, status="ok", message=message, details=details)


def fail(name: str, message: str, **details: object) -> ProbeResult:
    return ProbeResult(name=name, status="fail", message=message, details=details)


def unknown(name: str, message: str, **details: object) -> ProbeResult:
    return ProbeResult(name=name, status="unknown", message=message, details=details)


def parse_target(target: str) -> tuple[str, int, str]:
    parsed = urlparse(target if "://" in target else f"http://{target}")
    if not parsed.hostname:
        raise ValueError("target must include a hostname")

    if parsed.port:
        port = parsed.port
    elif parsed.scheme == "https":
        port = 443
    else:
        port = 80

    base_url = f"{parsed.scheme}://{parsed.netloc}"
    return parsed.hostname, port, base_url


def check_dns(hostname: str, port: int) -> ProbeResult:
    try:
        records = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        return fail("dns", f"DNS lookup failed for {hostname}", error=str(exc))

    addresses = sorted({record[4][0] for record in records})
    return ok("dns", f"resolved {hostname}", addresses=addresses)


def check_tcp(hostname: str, port: int, timeout_seconds: float) -> ProbeResult:
    started = perf_counter()
    try:
        with socket.create_connection((hostname, port), timeout=timeout_seconds):
            elapsed_ms = round((perf_counter() - started) * 1000, 2)
            return ok("tcp", f"connected to {hostname}:{port}", elapsed_ms=elapsed_ms)
    except OSError as exc:
        elapsed_ms = round((perf_counter() - started) * 1000, 2)
        return fail(
            "tcp",
            f"could not connect to {hostname}:{port}",
            elapsed_ms=elapsed_ms,
            error=str(exc),
        )


def check_http_health(base_url: str, timeout_seconds: float) -> ProbeResult:
    url = urljoin(f"{base_url.rstrip('/')}/", "health")
    started = perf_counter()
    try:
        response = httpx.get(url, timeout=timeout_seconds)
    except httpx.HTTPError as exc:
        return fail("service_health", f"health request failed for {url}", error=str(exc))

    elapsed_ms = round((perf_counter() - started) * 1000, 2)
    if 200 <= response.status_code < 300:
        return ok(
            "service_health",
            f"health endpoint returned {response.status_code}",
            url=url,
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
        )

    return fail(
        "service_health",
        f"health endpoint returned {response.status_code}",
        url=url,
        status_code=response.status_code,
        elapsed_ms=elapsed_ms,
        body=response.text[:500],
    )


def sample_latency(base_url: str, samples: int, timeout_seconds: float) -> ProbeResult:
    url = urljoin(f"{base_url.rstrip('/')}/", "query")
    durations: list[float] = []
    status_codes: list[int] = []

    for sequence in range(1, samples + 1):
        started = perf_counter()
        try:
            response = httpx.get(url, params={"sql": f"select {sequence}"}, timeout=timeout_seconds)
            status_codes.append(response.status_code)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return fail(
                "latency",
                f"latency sample failed at request {sequence}",
                url=url,
                completed_samples=len(durations),
                error=str(exc),
            )

        durations.append((perf_counter() - started) * 1000)

    ordered = sorted(durations)
    p95_index = max(0, min(len(ordered) - 1, round(len(ordered) * 0.95) - 1))
    return ok(
        "latency",
        f"completed {samples} latency samples",
        url=url,
        samples=samples,
        min_ms=round(min(durations), 2),
        avg_ms=round(mean(durations), 2),
        p95_ms=round(ordered[p95_index], 2),
        max_ms=round(max(durations), 2),
        status_codes=status_codes,
    )


def check_route(hostname: str, timeout_seconds: float) -> ProbeResult:
    commands = [
        ["ip", "route", "get", hostname],
        ["route", "get", hostname],
    ]

    for command in commands:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return unknown("route", f"route lookup timed out using {command[0]}", command=command)

        output = (completed.stdout or completed.stderr).strip()
        if completed.returncode == 0:
            return ok("route", f"route lookup succeeded using {command[0]}", command=command, output=output)

        return unknown(
            "route",
            f"route lookup returned {completed.returncode} using {command[0]}",
            command=command,
            output=output,
        )

    return unknown("route", "no supported route inspection command found")


def check_rejected_traffic(prometheus_url: str | None, timeout_seconds: float) -> ProbeResult:
    if not prometheus_url:
        return unknown("rejected_traffic", "Prometheus URL not provided")

    query = 'sum(increase(trafficgen_requests_total{outcome=~"http_error|network_error|server_error"}[5m]))'
    url = urljoin(f"{prometheus_url.rstrip('/')}/", "api/v1/query")
    try:
        response = httpx.get(url, params={"query": query}, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return unknown("rejected_traffic", "could not query Prometheus for rejected traffic", error=str(exc))

    result = payload.get("data", {}).get("result", [])
    value = 0.0
    if result:
        raw_value = result[0].get("value", [None, "0"])[1]
        value = float(raw_value)

    if value > 0:
        return fail("rejected_traffic", "recent rejected traffic detected", rejected_requests=value, query=query)

    return ok("rejected_traffic", "no recent rejected traffic detected", rejected_requests=value, query=query)


def diagnose(
    target: str,
    *,
    prometheus_url: str | None,
    samples: int,
    timeout_seconds: float,
) -> list[ProbeResult]:
    hostname, port, base_url = parse_target(target)
    return [
        check_dns(hostname, port),
        check_tcp(hostname, port, timeout_seconds),
        check_http_health(base_url, timeout_seconds),
        sample_latency(base_url, samples, timeout_seconds),
        check_route(hostname, timeout_seconds),
        check_rejected_traffic(prometheus_url, timeout_seconds),
    ]
