"""
Aegis backend entry point.

Run with:
    python main.py
or:
    uvicorn backend.main:app --reload --port 8000
"""

import json
import logging
import time
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from backend.api.routes import router as api_router
from backend.api.websocket import websocket_endpoint, websocket_incident_endpoint
from backend.config.settings import get_settings
from backend.orchestrator.coordinator import get_coordinator
from backend.orchestrator.monitor_loop import get_monitor_loop
from backend.services.db import run_migrations
from backend.services.qwen_client import QwenServiceUnavailable
from backend.services.startup_health import run_startup_health_check

settings = get_settings()

# ── Structured JSON logging ──────────────────────────────────────────────────

class JsonFormatter(logging.Formatter):
    """Emits every log record as a single JSON line — easy to ingest in
    Alibaba Cloud Log Service or any centralized log aggregator."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    root.handlers = [handler]


setup_logging()
logger = logging.getLogger("aegis.main")

# ── Rate limiter (100 req/min per IP) ────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Aegis API",
    description="Autonomous multi-agent incident response for cloud infrastructure.",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global error handlers ─────────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Request validation failed", "detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception on %s %s: %s\n%s",
        request.method,
        request.url.path,
        str(exc),
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "message": str(exc)},
    )


@app.exception_handler(QwenServiceUnavailable)
async def qwen_service_unavailable_handler(request: Request, exc: QwenServiceUnavailable) -> JSONResponse:
    logger.warning("Upstream Qwen service unavailable on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"error": "Upstream Qwen service unavailable", "message": str(exc)},
    )


# ── Request timing middleware ─────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(
        "HTTP %s %s -> %s in %sms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(api_router, prefix=settings.api_prefix)
app.websocket("/ws")(websocket_endpoint)
app.websocket("/ws/incidents/{incident_id}")(websocket_incident_endpoint)
app.websocket("/ws/{incident_id}")(websocket_incident_endpoint)


@app.get("/")
async def root():
    return {"service": "aegis", "status": "operational", "docs": "/docs"}


# ── Lifecycle ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Aegis backend starting up in '%s' mode", settings.environment)
    if not settings.qwen_api_key:
        logger.warning(
            "QWEN_API_KEY is not set — agent pipeline calls will fail until it's configured in .env. "
            "The API will still serve demo data for the dashboard."
        )
    await run_migrations()
    startup_health = await run_startup_health_check()
    if startup_health["ok"]:
        logger.info("Startup health check passed: %s", startup_health["checkedAt"])
    else:
        logger.warning("Startup health check reported issues: %s", startup_health["checks"])
    coordinator = get_coordinator()
    monitor = get_monitor_loop(coordinator)
    monitor.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Aegis backend shutting down")
    coordinator = get_coordinator()
    monitor = get_monitor_loop(coordinator)
    await monitor.stop()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.environment == "development")
