import asyncio
from contextlib import asynccontextmanager
from time import perf_counter, time
from urllib.parse import urlencode

import httpx
from fastapi import Depends, FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from trafficgen.settings import Settings, get_settings

TRAFFIC_REQUESTS = Counter(
    "trafficgen_requests_total",
    "Total synthetic requests sent by the traffic generator.",
    ["target", "outcome", "status_code"],
)
TRAFFIC_LATENCY = Histogram(
    "trafficgen_request_duration_seconds",
    "Synthetic client-observed request latency.",
    ["target"],
)
TRAFFIC_SLO_VIOLATIONS = Counter(
    "trafficgen_slo_violations_total",
    "Synthetic requests that exceeded the configured latency SLO.",
    ["target"],
)
TRAFFIC_CONFIG_RPS = Gauge(
    "trafficgen_config_requests_per_second",
    "Configured synthetic request rate.",
)
TRAFFIC_LAST_SUCCESS = Gauge(
    "trafficgen_last_success_timestamp_seconds",
    "Unix timestamp of the most recent successful synthetic request.",
    ["target"],
)


def query_url(settings: Settings, sequence: int) -> str:
    base = str(settings.target_base_url).rstrip("/")
    params = urlencode({"sql": f"select {sequence}"})
    return f"{base}/query?{params}"


class TrafficWorker:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.sent = 0
        self.successes = 0
        self.failures = 0
        self.last_error: str | None = None
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        if self.running or not self.settings.traffic_enabled:
            return

        TRAFFIC_CONFIG_RPS.set(self.settings.requests_per_second)
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            await self._task

    async def _run(self) -> None:
        interval_seconds = 1 / self.settings.requests_per_second
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            while not self._stop.is_set():
                await self.send_once(client)
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=interval_seconds)
                except TimeoutError:
                    continue

    async def send_once(self, client: httpx.AsyncClient) -> None:
        self.sent += 1
        target = str(self.settings.target_base_url).rstrip("/")
        started = perf_counter()
        status_code = "error"

        try:
            response = await client.get(query_url(self.settings, self.sent))
            elapsed_seconds = perf_counter() - started
            status_code = str(response.status_code)
            outcome = "success" if response.status_code < 500 else "server_error"
            response.raise_for_status()
            self.successes += 1
            self.last_error = None
            TRAFFIC_LAST_SUCCESS.labels(target=target).set(time())
        except httpx.HTTPStatusError as exc:
            elapsed_seconds = perf_counter() - started
            outcome = "http_error"
            status_code = str(exc.response.status_code)
            self.failures += 1
            self.last_error = str(exc)
        except httpx.HTTPError as exc:
            elapsed_seconds = perf_counter() - started
            outcome = "network_error"
            self.failures += 1
            self.last_error = str(exc)

        TRAFFIC_REQUESTS.labels(target=target, outcome=outcome, status_code=status_code).inc()
        TRAFFIC_LATENCY.labels(target=target).observe(elapsed_seconds)
        if elapsed_seconds * 1000 > self.settings.slo_latency_ms:
            TRAFFIC_SLO_VIOLATIONS.labels(target=target).inc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    worker = TrafficWorker(settings)
    app.state.traffic_worker = worker
    await worker.start()
    yield
    await worker.stop()


app = FastAPI(
    title="Network Lab Traffic Generator",
    description="Synthetic client traffic for the distributed database network lab.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str | bool | float | int]:
    worker: TrafficWorker | None = getattr(app.state, "traffic_worker", None)
    return {
        "status": "healthy",
        "target_base_url": str(settings.target_base_url).rstrip("/"),
        "traffic_enabled": settings.traffic_enabled,
        "running": bool(worker and worker.running),
        "requests_per_second": settings.requests_per_second,
        "slo_latency_ms": settings.slo_latency_ms,
    }


@app.get("/stats")
def stats() -> dict[str, str | bool | int | None]:
    worker: TrafficWorker | None = getattr(app.state, "traffic_worker", None)
    if worker is None:
        return {
            "running": False,
            "sent": 0,
            "successes": 0,
            "failures": 0,
            "last_error": None,
        }

    return {
        "running": worker.running,
        "sent": worker.sent,
        "successes": worker.successes,
        "failures": worker.failures,
        "last_error": worker.last_error,
    }


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})
