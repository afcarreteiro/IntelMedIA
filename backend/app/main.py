from contextlib import asynccontextmanager
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.config import settings
from app.database import init_db
from app.routes import auth, catalog, sessions, stream

try:
    from prometheus_client import Counter, Histogram, generate_latest
except ModuleNotFoundError:
    class _NullMetric:
        def labels(self, **_kwargs):
            return self

        def inc(self):
            return None

        def observe(self, _value):
            return None

    def Counter(*_args, **_kwargs):
        return _NullMetric()

    def Histogram(*_args, **_kwargs):
        return _NullMetric()

    def generate_latest():
        return b""


request_count = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])
request_duration = Histogram("http_request_duration_seconds", "HTTP request duration")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(sessions.router)
app.include_router(stream.router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "transcript_retention": settings.transcript_retention,
        "region": settings.region,
    }


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")


@app.middleware("http")
async def track_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    request_count.labels(method=request.method, endpoint=request.url.path).inc()
    request_duration.observe(duration)

    return response
