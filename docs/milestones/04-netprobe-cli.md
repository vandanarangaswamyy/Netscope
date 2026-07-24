# Milestone 4: `netprobe` Diagnostics CLI

## Networking Concept

Operators need fast checks that separate name resolution, port reachability, route selection, service health, latency, and rejected traffic. A single failed request only says that the path is broken; layered diagnostics identify where it is broken.

This milestone adds `netprobe`, a Python CLI that can run from the host or from inside the private Docker network:

- Host mode checks the published Nginx and Prometheus endpoints on `localhost`.
- Docker-network mode checks service DNS names such as `nginx` and `prometheus`, closer to how private DNS will work in AWS.

## Proposed Folder Structure

```text
.
├── docker-compose.yml
├── docs/milestones/04-netprobe-cli.md
├── infra/netprobe/Dockerfile
├── netprobe
│   ├── __init__.py
│   ├── cli.py
│   └── probes.py
└── tests/netprobe
    ├── test_cli.py
    └── test_probes.py
```

## Implemented Feature

This milestone adds:

- `netprobe diagnose`, an installable Python console script.
- DNS resolution checks using `socket.getaddrinfo`.
- TCP connectivity checks using `socket.create_connection`.
- HTTP service health checks against `/health`.
- Client-observed latency sampling against `/query`.
- Route inspection using `ip route get` or `route get` when available.
- Rejected traffic detection using Prometheus `trafficgen_requests_total` outcome labels.
- Optional JSON output with `--json`.
- A Compose `tools` profile so diagnostics can run from the private Docker network.

## Automated Tests

Run:

```bash
uv run pytest
```

The tests verify:

- Target parsing.
- TCP success behavior with a local socket.
- HTTP health handling.
- Latency failure handling.
- Route fallback behavior.
- Prometheus rejected-traffic parsing.
- CLI text, JSON, and exit-code behavior.

## Manual Verification

Start the cluster:

```bash
docker compose up --build
```

Run from the host against published local ports:

```bash
uv run netprobe diagnose --target http://localhost:8080 --prometheus-url http://localhost:9090
```

Run with JSON output:

```bash
uv run netprobe diagnose --target http://localhost:8080 --prometheus-url http://localhost:9090 --samples 2 --json
```

Run from inside the private Docker network:

```bash
docker compose --profile tools run --rm netprobe diagnose --target http://nginx:8080 --prometheus-url http://prometheus:9090
```

Expected successful checks:

```text
[OK] dns
[OK] tcp
[OK] service_health
[OK] latency
[OK] rejected_traffic
```

The route check may return `UNKNOWN` if the container or host does not have a supported route inspection tool. That is acceptable for this milestone; missing routes will become a controlled failure scenario later.

Clean up:

```bash
docker compose down
```

## Expected Result

`netprobe` should confirm that Nginx resolves, port `8080` is reachable, `/health` returns success, `/query` latency samples complete, and Prometheus reports no recent rejected synthetic traffic.
