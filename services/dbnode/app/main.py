from time import perf_counter, sleep

from fastapi import Depends, FastAPI, Query, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from app.settings import Settings, get_settings

REQUEST_COUNT = Counter(
    "dbnode_http_requests_total",
    "Total HTTP requests served by a simulated database node.",
    ["method", "path", "status_code", "node_id"],
)
REQUEST_LATENCY = Histogram(
    "dbnode_http_request_duration_seconds",
    "HTTP request latency for a simulated database node.",
    ["method", "path", "node_id"],
)
NODE_INFO = Gauge(
    "dbnode_info",
    "Static metadata for a simulated database node.",
    ["node_id", "role"],
)

app = FastAPI(
    title="Distributed Analytics Node Simulator",
    description="Open-source stand-in for a distributed database service node.",
    version="0.1.0",
)


def resolve_settings() -> Settings:
    settings_provider = app.dependency_overrides.get(get_settings, get_settings)
    return settings_provider()


@app.middleware("http")
async def collect_request_metrics(request: Request, call_next):
    settings = resolve_settings()
    started = perf_counter()
    response = await call_next(request)
    elapsed_seconds = perf_counter() - started
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)

    REQUEST_COUNT.labels(
        method=request.method,
        path=path,
        status_code=str(response.status_code),
        node_id=settings.node_id,
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        path=path,
        node_id=settings.node_id,
    ).observe(elapsed_seconds)
    return response


@app.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "status": "healthy",
        "node_id": settings.node_id,
        "role": settings.node_role,
    }


@app.get("/node")
def node(settings: Settings = Depends(get_settings)) -> dict[str, str | int]:
    return {
        "node_id": settings.node_id,
        "role": settings.node_role,
        "simulated_latency_ms": settings.simulated_latency_ms,
    }


@app.get("/query")
def query(
    sql: str = Query(default="select 1", min_length=1, max_length=500),
    settings: Settings = Depends(get_settings),
) -> dict[str, str | int | float]:
    started = perf_counter()

    if settings.simulated_latency_ms:
        sleep(settings.simulated_latency_ms / 1000)

    elapsed_ms = round((perf_counter() - started) * 1000, 2)
    return {
        "node_id": settings.node_id,
        "status": "ok",
        "sql": sql,
        "simulated_latency_ms": settings.simulated_latency_ms,
        "elapsed_ms": elapsed_ms,
    }


@app.get("/metrics")
def metrics(settings: Settings = Depends(get_settings)) -> Response:
    NODE_INFO.labels(node_id=settings.node_id, role=settings.node_role).set(1)
    return Response(content=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})
