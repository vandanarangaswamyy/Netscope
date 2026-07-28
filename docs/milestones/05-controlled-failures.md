# Milestone 5: Controlled Local Failure Scenarios

## Networking Concept

Network labs are useful when failures are repeatable. A distributed database client path can degrade because one backend is slow, one backend is unhealthy, or the load balancer continues sending traffic to a bad target. This milestone introduces controlled application-level failures that make those symptoms visible through Nginx, Prometheus, Grafana, traffic generation, and `netprobe`.

This is intentionally local and reversible:

- The default `docker-compose.yml` remains the healthy baseline.
- `docker-compose.failures.yml` overlays failure settings.
- Service node ports remain private on the Docker network.

## Proposed Folder Structure

```text
.
├── docker-compose.yml
├── docker-compose.failures.yml
├── docs/milestones/05-controlled-failures.md
└── services/dbnode
    ├── dbnode
    │   ├── main.py
    │   └── settings.py
    └── tests/test_main.py
```

## Implemented Feature

This milestone adds failure injection settings to each simulated database node:

- `FORCE_UNHEALTHY`: makes `/health` return an error.
- `FAIL_QUERIES_WHEN_UNHEALTHY`: makes `/query` fail when the node is unhealthy.
- `HEALTH_FAILURE_STATUS_CODE`: controls the failure HTTP status code.
- `SIMULATED_LATENCY_MS`: already existed and is now used in the failure overlay.

The failure overlay does this:

- `node-b`: increases latency to `750ms`.
- `node-c`: returns `503` for health and query requests.
- `trafficgen`: lowers the latency SLO to `100ms` so slow traffic becomes visible quickly.

Nginx and Prometheus now wait for containers to start rather than requiring every node health check to pass. That allows the lab to run while one node is intentionally unhealthy.

## Automated Tests

Run:

```bash
uv run pytest
```

The tests verify:

- Forced unhealthy health responses.
- Query failures while a node is unhealthy.
- Optional query continuation when only health should fail.
- Validation for failure status codes.
- Existing node, traffic generator, and `netprobe` behavior still works.

Validate the failure overlay:

```bash
docker compose -f docker-compose.yml -f docker-compose.failures.yml config
```

## Manual Verification

Start the healthy baseline first:

```bash
docker compose up --build
```

Confirm normal diagnostics:

```bash
uv run netprobe diagnose --target http://localhost:8080 --prometheus-url http://localhost:9090 --samples 3
```

Stop the baseline:

```bash
docker compose down
```

Start the failure overlay:

```bash
docker compose -f docker-compose.yml -f docker-compose.failures.yml up --build
```

Inspect the configured node behavior:

```bash
for i in 1 2 3 4 5 6; do curl -s http://localhost:8080/node; echo; done
```

Expected observations:

- `node-b` reports `simulated_latency_ms` as `750`.
- `node-c` reports `force_unhealthy` as `true`.

Generate traffic and inspect traffic generator stats:

```bash
sleep 30
curl http://localhost:9000/stats
```

Run diagnostics:

```bash
uv run netprobe diagnose --target http://localhost:8080 --prometheus-url http://localhost:9090 --samples 6
```

Expected failure-mode observations:

- Some `/query` requests may return `503` when Nginx routes to `node-c`.
- Traffic generator `failures` should increase.
- Grafana `Traffic Generator Overview` should show SLO violations and/or error outcomes.
- `netprobe` may fail `latency` or `rejected_traffic`, which is expected under this overlay.

Check container health:

```bash
docker compose -f docker-compose.yml -f docker-compose.failures.yml ps
```

`node-c` should show as unhealthy.

Clean up:

```bash
docker compose -f docker-compose.yml -f docker-compose.failures.yml down
```

Return to healthy baseline:

```bash
docker compose up --build
```

## Expected Result

The failure overlay should make degradation visible without changing source code or exposing service node ports. Removing the overlay should return the lab to the healthy baseline.
