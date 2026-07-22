# Cloud Network Reliability Lab

This lab simulates the network reliability concerns of a distributed analytics database without requiring proprietary Teradata software. It uses open tooling to model service nodes, load balancing, DNS, routing, observability, failure injection, diagnostics, and low-cost AWS infrastructure.

## Milestone Plan

1. Local three-node service cluster behind Nginx.
2. Prometheus metrics and Grafana dashboards.
3. Traffic generator and baseline latency/error SLOs.
4. `netprobe` Python CLI for DNS, TCP, port, latency, route, health, and rejection diagnostics.
5. Controlled local failure scenarios: blocked ports, broken DNS, unhealthy nodes, missing routes, and increased latency.
6. Terraform AWS network foundation: VPC across two availability zones, public/private subnets, route tables, NAT gateway, security groups, private Route 53 DNS, internal load balancer, VPC Flow Logs, and CloudWatch.
7. AWS deployment of service nodes, monitoring hooks, and cleanup workflow.

## Current Milestone

Milestone 3 adds synthetic traffic and baseline SLO metrics to the local cluster:

- Three FastAPI service nodes: `node-a`, `node-b`, and `node-c`.
- One Nginx load balancer on `localhost:8080`.
- One traffic generator on `localhost:9000`, sending synthetic client requests through Nginx.
- Prometheus on `localhost:9090`, scraping each private node directly.
- Grafana on `localhost:3000`, pre-provisioned with Prometheus dashboards.
- Health, identity, query, and metrics endpoints for validating load balancing and observability.
- Automated pytest coverage for service behavior.
- GitHub Actions workflow for Python tests.

## Quick Start

Install and run tests:

```bash
uv run pytest
```

Run the local cluster:

```bash
docker compose up --build
```

Verify the load balancer:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/node
curl http://localhost:8080/metrics
curl http://localhost:9000/health
curl http://localhost:9000/stats
curl "http://localhost:9090/api/v1/targets?state=active"
```

Open Grafana at `http://localhost:3000` and log in with `admin` / `lab-admin`.

Stop and remove local containers:

```bash
docker compose down
```

## Security And Cost Defaults

- Local service containers are only reachable through Nginx; their ports are not published to the host.
- AWS resources will be private by default unless a later milestone explicitly needs public ingress.
- Terraform-managed resources will be designed so `terraform destroy` removes the lab cleanly.
- AWS deployment will favor low-cost primitives and short-lived test environments.
