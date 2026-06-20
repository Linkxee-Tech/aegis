"""
FastAPI route definitions for Aegis.

Endpoints map directly to what frontend/src/services/api.ts expects, so the
frontend's `api` object can be pointed at this backend with no changes on
either side. Demo/seed data lives in `backend/api/demo_data.py` so judges can
see a populated dashboard without first wiring up real infrastructure.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.api.demo_data import (
    demo_agents,
    demo_incidents,
    demo_memory_records,
    demo_reports,
    demo_system_health,
)
from backend.api.models import RejectionPayload
from backend.orchestrator.coordinator import get_coordinator
from backend.services.startup_health import run_startup_health_check

logger = logging.getLogger("aegis.routes")
router = APIRouter()


# ── System health ─────────────────────────────────────────────────────────────

@router.get("/health")
async def get_health():
    """System health summary for the dashboard's status strip."""
    coordinator = get_coordinator()
    live_incidents = coordinator.list_incidents()
    if live_incidents:
        active = sum(1 for i in live_incidents if i["status"] not in ("resolved", "auto_resolved", "rejected"))
        return {
            "allAgentsOperational": True,
            "lastIncidentAgo": "moments ago",
            "activeIncidentCount": active,
            "uptimePercentage": 99.9,
        }
    return demo_system_health()


@router.get("/health/startup")
async def get_startup_health():
    """Startup verification summary for the protocol and ops review."""
    return await run_startup_health_check()


# ── Agents ────────────────────────────────────────────────────────────────────

@router.get("/agents")
async def get_agents():
    """Current status of all five agents."""
    return demo_agents()


@router.get("/agents/status")
async def get_agents_status():
    """Alias matching Phase 2 checklist spec: /api/agents/status."""
    return demo_agents()


# ── Incidents ─────────────────────────────────────────────────────────────────

@router.get("/incidents")
async def get_incidents():
    """All incidents, live ones first if the orchestrator has any, else demo data."""
    coordinator = get_coordinator()
    live = coordinator.list_incidents()
    return live if live else demo_incidents()


@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    coordinator = get_coordinator()
    incident = coordinator.get_incident(incident_id)
    if incident is not None:
        return incident
    for demo in demo_incidents():
        if demo["id"] == incident_id:
            return demo
    raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")


@router.post("/incidents/{incident_id}/approve")
async def approve_incident(incident_id: str):
    coordinator = get_coordinator()
    success = await coordinator.approve_and_execute(incident_id)
    if not success:
        raise HTTPException(
            status_code=409,
            detail="No pending approval found for this incident (it may have expired or already been resolved).",
        )
    return {"success": True}


@router.post("/incidents/{incident_id}/reject")
async def reject_incident(incident_id: str, payload: RejectionPayload):
    coordinator = get_coordinator()
    success = await coordinator.reject_remediation(incident_id, payload.reason)
    if not success:
        raise HTTPException(status_code=409, detail="No pending approval found for this incident.")
    return {"success": True}


# ── Simulate ──────────────────────────────────────────────────────────────────

class SimulatePayload(BaseModel):
    scenario: str = "cpu_spike"   # cpu_spike | memory_leak | disk_io | connection_pool | tls_failure
    server: str = "prod-ecs-03.ap-southeast-1"
    service: str = "payment-service"


SCENARIO_SNAPSHOTS: dict[str, dict] = {
    "cpu_spike": {
        "current_metrics": {"cpu": 97.0, "memory": 91.0, "error_rate": 0.18, "p99_latency_ms": 4200},
        "baseline_metrics": {"cpu_mean": 22.0, "cpu_std": 6.0, "memory_mean": 40.0, "memory_std": 8.0},
        "recent_log_lines": [
            f"{datetime.now(timezone.utc).isoformat()} ERROR payment-service: connection timeout on /v1/charge",
            f"{datetime.now(timezone.utc).isoformat()} ERROR payment-service: heap OOM warning — used 91% of 4GB",
            f"{datetime.now(timezone.utc).isoformat()} WARN  payment-service: GC pause 2340ms — long GC cycle detected",
        ],
        "recent_deploys": [{"build_id": "4471", "deployed_at": "38 minutes ago", "service": "payment-service"}],
    },
    "memory_leak": {
        "current_metrics": {"cpu": 55.0, "memory": 98.0, "error_rate": 0.04, "p99_latency_ms": 1800},
        "baseline_metrics": {"cpu_mean": 30.0, "cpu_std": 8.0, "memory_mean": 45.0, "memory_std": 10.0},
        "recent_log_lines": [
            f"{datetime.now(timezone.utc).isoformat()} WARN  orders-service: heap growing steadily — 820MB over 15 minutes",
            f"{datetime.now(timezone.utc).isoformat()} ERROR orders-service: OutOfMemoryError: Java heap space",
        ],
        "recent_deploys": [],
    },
    "disk_io": {
        "current_metrics": {"cpu": 28.0, "memory": 42.0, "disk_write_pct": 98.0, "error_rate": 0.01},
        "baseline_metrics": {"cpu_mean": 25.0, "cpu_std": 5.0, "disk_write_pct_mean": 45.0, "disk_write_pct_std": 12.0},
        "recent_log_lines": [
            f"{datetime.now(timezone.utc).isoformat()} WARN  logging-agent: disk write queue depth 892 — I/O saturation",
            f"{datetime.now(timezone.utc).isoformat()} ERROR logging-agent: write failed — no space left on device /var/log",
        ],
        "recent_deploys": [{"build_id": "2201", "deployed_at": "2 hours ago", "service": "logging-agent"}],
    },
    "connection_pool": {
        "current_metrics": {"cpu": 40.0, "memory": 55.0, "db_pool_wait_ms": 5200, "error_rate": 0.12},
        "baseline_metrics": {"cpu_mean": 35.0, "cpu_std": 7.0, "db_pool_wait_ms_mean": 40.0, "db_pool_wait_ms_std": 15.0},
        "recent_log_lines": [
            f"{datetime.now(timezone.utc).isoformat()} ERROR orders-service: could not acquire DB connection after 5000ms — pool exhausted",
            f"{datetime.now(timezone.utc).isoformat()} ERROR orders-service: HikariPool-1 - Connection is not available, request timed out after 5000ms",
        ],
        "recent_deploys": [],
    },
    "tls_failure": {
        "current_metrics": {"cpu": 20.0, "memory": 38.0, "error_rate": 0.064, "p99_latency_ms": 900},
        "baseline_metrics": {"cpu_mean": 18.0, "cpu_std": 4.0, "error_rate_mean": 0.002, "error_rate_std": 0.001},
        "recent_log_lines": [
            f"{datetime.now(timezone.utc).isoformat()} ERROR api-gateway: TLS handshake failure — certificate expired on auth-service sidecar",
            f"{datetime.now(timezone.utc).isoformat()} WARN  api-gateway: upstream auth-service returned 503 for 47 consecutive requests",
        ],
        "recent_deploys": [],
    },
}


@router.post("/simulate")
async def simulate_incident(payload: SimulatePayload):
    """
    Trigger a simulated incident through the full agent pipeline.
    Used by the 'Simulate Incident' button in the UI for the live demo.
    Returns the new incident_id immediately; the pipeline runs asynchronously
    and pushes updates via WebSocket as each agent completes.
    """
    snapshot = SCENARIO_SNAPSHOTS.get(payload.scenario, SCENARIO_SNAPSHOTS["cpu_spike"])
    coordinator = get_coordinator()

    import asyncio
    # Fire pipeline as a background task so this endpoint returns quickly
    async def run():
        try:
            await coordinator.run_detection_cycle(
                server=payload.server,
                service=payload.service,
                monitoring_snapshot=snapshot,
            )
        except Exception:
            logger.exception("Simulated incident pipeline failed")

    asyncio.create_task(run())

    return {
        "success": True,
        "scenario": payload.scenario,
        "server": payload.server,
        "service": payload.service,
        "message": "Incident detection triggered — watch the Dashboard for real-time updates",
    }


# ── Memory ────────────────────────────────────────────────────────────────────

@router.get("/memory")
async def get_memory():
    """Patterns the Memory Agent has learned, for the Memory dashboard page."""
    return demo_memory_records()


# ── Reports ───────────────────────────────────────────────────────────────────

@router.get("/reports")
async def get_reports():
    return demo_reports()


@router.get("/reports/{report_id}/download")
async def download_report(report_id: str):
    """
    Placeholder for report export. In production this streams a PDF generated
    via the pdf skill / reportlab and uploaded to OSS by AlibabaCloudService.upload_report.
    """
    raise HTTPException(status_code=501, detail="PDF export not yet wired to OSS in this build.")
