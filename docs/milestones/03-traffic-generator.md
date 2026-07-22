# Milestone 3: Traffic Generator And Baseline SLOs

## Networking Concept

Network reliability testing needs a repeatable client workload. A load balancer can look healthy while real client requests still experience timeouts, resets, slow responses, or elevated error rates. This milestone adds a synthetic client inside the same private Docker network that continuously calls the Nginx endpoint and records client-observed behavior.

This creates two useful perspectives:

- Service-side metrics from the database nodes.
- Client-side metrics from the traffic generator.

Comparing the two helps distinguish node processing latency from network path or load balancer issues.

## Proposed Folder Structure

```text
.
├── docker-compose.yml
├── docs/milestones/03-traffic-generator.md
├── infra
│   ├── grafana/dashboards/trafficgen-overview.json
│   └── prometheus/prometheus.yml
└── services
    ├── dbnode
    │   └── dbnode/main.py
    └── trafficgen
        ├── Dockerfile
        ├── trafficgen
        │   ├── __init__.py
        │   ├── main.py
        │   └── settings.py
        └── tests
            ├── test_settings.py
            └── test_trafficgen_main.py
```

## Implemented Feature

This milestone adds a `trafficgen` service that:

- Sends continuous `GET /query` requests through Nginx to simulate client traffic.
- Uses configurable request rate, timeout, and latency SLO settings.
- Exposes `GET /health`, `GET /stats`, and `GET /metrics` on port `9000`.
- Emits Prometheus metrics for request outcomes, client-observed latency, configured request rate, last success time, and latency SLO violations.
- Adds a Grafana dashboard named `Traffic Generator Overview`.

Default local settings:

```text
TARGET_BASE_URL=http://nginx:8080
REQUESTS_PER_SECOND=2
REQUEST_TIMEOUT_SECONDS=2
SLO_LATENCY_MS=250
```

## Automated Tests

Run:

```bash
uv run pytest
```

The tests verify:

- Traffic generator settings validation.
- Query URL construction.
- Health endpoint configuration reporting.
- Successful synthetic request accounting.
- Network error accounting.
- Existing node and monitoring tests still pass.

## Manual Verification

Start the cluster:

```bash
docker compose up --build
```

Check the traffic generator:

```bash
curl http://localhost:9000/health
curl http://localhost:9000/stats
curl http://localhost:9000/metrics
```

Wait 30 seconds, then check stats again:

```bash
curl http://localhost:9000/stats
```

Check Prometheus targets:

```bash
curl "http://localhost:9090/api/v1/targets?state=active"
```

Open Grafana:

```text
http://localhost:3000
```

Log in with:

```text
username: admin
password: lab-admin
```

Open these dashboards:

```text
Network Reliability Lab / DB Node Network Overview
Network Reliability Lab / Traffic Generator Overview
```

Clean up:

```bash
docker compose down
```

## Expected Result

Prometheus should show `dbnodes` and `trafficgen` targets as healthy. The traffic generator stats should show increasing `sent` and `successes` counts, and Grafana should display synthetic request rate, client p95 latency, configured request rate, and latency SLO violations.
