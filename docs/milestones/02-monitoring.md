# Milestone 2: Prometheus And Grafana Monitoring

## Networking Concept

Reliable distributed systems need visibility from both the client path and the internal node path. In this milestone, Nginx still represents the client-facing endpoint, while Prometheus connects directly to each private service node on the Docker network.

This models an AWS design where application traffic reaches an internal load balancer, but monitoring systems scrape private targets by service discovery or private DNS. The service nodes still do not publish host ports.

## Proposed Folder Structure

```text
.
├── docker-compose.yml
├── docs/milestones/02-monitoring.md
├── infra
│   ├── grafana
│   │   ├── dashboards/dbnode-overview.json
│   │   └── provisioning
│   │       ├── dashboards/dashboards.yml
│   │       └── datasources/prometheus.yml
│   ├── nginx/nginx.conf
│   └── prometheus/prometheus.yml
└── services/dbnode
    ├── app/main.py
    └── tests/test_main.py
```

## Implemented Feature

This milestone adds:

- `GET /metrics` on every FastAPI node using Prometheus exposition format.
- Request counters labeled by method, path, status code, and node ID.
- Request latency histograms labeled by method, path, and node ID.
- A node metadata gauge exposing each node ID and role.
- Prometheus scraping `node-a:8000`, `node-b:8000`, and `node-c:8000` over the private Compose network.
- Grafana provisioning for the Prometheus datasource and a starter dashboard.

## Automated Tests

Run:

```bash
uv run pytest
```

The tests verify:

- `/metrics` emits Prometheus text format.
- Node metadata appears in metrics output.
- Application requests are counted with node labels.
- Existing health, node identity, query latency, and settings validation behavior still works.

## Manual Verification

Start the cluster:

```bash
docker compose up --build
```

Generate a little traffic:

```bash
for i in 1 2 3 4 5 6; do curl -s "http://localhost:8080/query?sql=select%20$i" >/dev/null; done
```

Check node metrics through the load balancer:

```bash
curl http://localhost:8080/metrics
```

Check Prometheus target health:

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

Open the `Network Reliability Lab / DB Node Network Overview` dashboard.

Clean up:

```bash
docker compose down
```

Remove persisted local observability data if you want a completely fresh run:

```bash
docker compose down --volumes
```

## Expected Result

Prometheus should show all three `dbnodes` targets as healthy. Grafana should show request rate, p95 request latency, and discovered nodes after you generate traffic.
