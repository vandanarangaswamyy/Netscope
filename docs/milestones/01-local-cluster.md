# Milestone 1: Local Service Cluster Behind Nginx

## Networking Concept

Distributed analytics platforms usually separate client entry points from internal worker nodes. Clients connect to a stable endpoint, while the platform routes requests to healthy nodes behind that endpoint. This milestone models that pattern locally:

- `nginx` is the client-facing endpoint.
- `node-a`, `node-b`, and `node-c` are private backend service nodes.
- Docker Compose DNS lets Nginx resolve backend containers by service name.
- Only the load balancer publishes a host port, which mirrors the later AWS pattern where service nodes live in private subnets.

## Proposed Folder Structure

```text
.
├── .github/workflows/ci.yml
├── docker-compose.yml
├── docs/milestones/01-local-cluster.md
├── infra/nginx/nginx.conf
├── pyproject.toml
└── services/dbnode
    ├── Dockerfile
    ├── app
    │   ├── __init__.py
    │   ├── main.py
    │   └── settings.py
    └── tests
        └── test_main.py
```

## Implemented Feature

This milestone implements a reusable FastAPI service node and runs three node instances behind Nginx. Each node exposes:

- `GET /health`: liveness and identity for load balancer checks.
- `GET /node`: node metadata that makes round-robin behavior visible.
- `GET /query`: a simulated analytics query endpoint with configurable latency.

## Automated Tests

Run:

```bash
uv run pytest
```

The tests verify:

- Healthy node responses.
- Node identity is read from environment-style settings.
- Simulated query latency is included in responses.
- Invalid latency configuration is rejected.

## Manual Verification

Start the cluster:

```bash
docker compose up --build
```

In another terminal, verify Nginx can reach the service nodes:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/node
curl "http://localhost:8080/query?sql=select%201"
```

Run this a few times to see requests rotate across nodes:

```bash
for i in 1 2 3 4 5 6; do curl -s http://localhost:8080/node; echo; done
```

Clean up:

```bash
docker compose down
```

## Expected Result

The load balancer should return successful responses from `node-a`, `node-b`, and `node-c` without publishing any node container ports directly to the host.
