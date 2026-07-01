"""
FastAPI route definitions for Aegis.

Endpoints map directly to what frontend/src/services/api.ts expects, so the
frontend's `api` object can be pointed at this backend with no changes on
either side. Demo/seed data lives in `backend/api/demo_data.py` so judges can
see a populated dashboard without first wiring up real infrastructure.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from backend.api.demo_data import (
    demo_agents,
    demo_incidents,
    demo_memory_records,
    demo_reports,
    demo_system_health,
)
from backend.api.models import AdminOverview, AdminServiceStatus, RejectionPayload
from backend.config.settings import get_settings
from backend.orchestrator.coordinator import get_coordinator
from backend.services.auth import require_roles
from backend.services.alibaba_cloud import AlibabaCloudNotConfiguredError, AlibabaCloudService
from backend.services.report_export import build_report_filename, build_report_pdf
from backend.services.startup_health import run_startup_health_check

logger = logging.getLogger("aegis.routes")
router = APIRouter()


# ── System health ─────────────────────────────────────────────────────────────

@router.get("/health", dependencies=[Depends(require_roles("viewer", "operator", "admin"))])
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


@router.get("/health/startup", dependencies=[Depends(require_roles("viewer", "operator", "admin"))])
async def get_startup_health():
    """Startup verification summary for the protocol and ops review."""
    return await run_startup_health_check()


@router.get("/admin/overview", dependencies=[Depends(require_roles("admin"))])
async def get_admin_overview() -> AdminOverview:
    settings = get_settings()
    coordinator = get_coordinator()
    live_incidents = coordinator.list_incidents()
    startup_health = await run_startup_health_check()
    incident_count = len(live_incidents)
    pending_approvals = sum(1 for incident in live_incidents if incident.get("status") == "awaiting_approval")
    monitored_servers = settings.monitored_servers

    service_matrix = [
        AdminServiceStatus(
            name="Qwen Cloud",
            status="Connected" if bool(settings.qwen_api_key) else "Needs attention",
            detail="Qwen API key configured" if bool(settings.qwen_api_key) else "Add QWEN_API_KEY to .env",
        ),
        AdminServiceStatus(
            name="PostgreSQL",
            status="Configured" if bool(settings.database_url) else "Needs attention",
            detail="Database URL available" if bool(settings.database_url) else "Set DATABASE_URL in .env",
        ),
        AdminServiceStatus(
            name="Redis",
            status="Configured" if bool(settings.redis_url) else "Needs attention",
            detail="Redis URL available" if bool(settings.redis_url) else "Set REDIS_URL in .env",
        ),
        AdminServiceStatus(
            name="Alibaba Cloud",
            status="Ready" if bool(settings.alibaba_cloud_access_key) else "Demo mode",
            detail="Cloud credentials detected" if bool(settings.alibaba_cloud_access_key) else "OSS/CloudMonitor fall back to demo paths",
        ),
        AdminServiceStatus(
            name="WebSocket Stream",
            status="Live",
            detail=f"{incident_count} incident(s) currently tracked",
        ),
    ]

    recent_signals = [check["name"] for check in startup_health.get("checks", []) if not check["ok"]][:4]
    if not recent_signals:
        recent_signals = ["No startup warnings", "All core modules imported cleanly"]

    return AdminOverview(
        environment=settings.environment,
        apiPrefix=settings.api_prefix,
        authEnabled=bool(settings.auth_enabled),
        authMode="Protected" if bool(settings.auth_enabled) else "Open demo",
        backendStatus="operational" if startup_health.get("ok", False) else "degraded",
        startupOk=bool(startup_health.get("ok", False)),
        startupCheckedAt=startup_health.get("checkedAt", datetime.now(timezone.utc).isoformat()),
        qwenConfigured=bool(settings.qwen_api_key),
        databaseConfigured=bool(settings.database_url),
        redisConfigured=bool(settings.redis_url),
        monitoredServers=monitored_servers,
        agentCount=5,
        activeIncidentCount=incident_count,
        pendingApprovals=pending_approvals,
        reportCount=len(demo_reports()),
        memoryRecordCount=len(demo_memory_records()),
        docsUrl="/docs",
        supportedScenarios=["cpu_spike", "memory_leak", "disk_io", "connection_pool", "tls_failure"],
        serviceMatrix=service_matrix,
        recentSignals=recent_signals,
    )


# ── Agents ────────────────────────────────────────────────────────────────────

@router.get("/agents", dependencies=[Depends(require_roles("viewer", "operator", "admin"))])
async def get_agents():
    """Current status of all five agents."""
    return demo_agents()


@router.get("/agents/status", dependencies=[Depends(require_roles("viewer", "operator", "admin"))])
async def get_agents_status():
    """Alias matching Phase 2 checklist spec: /api/agents/status."""
    return demo_agents()


# ── Incidents ─────────────────────────────────────────────────────────────────

@router.get("/incidents", dependencies=[Depends(require_roles("viewer", "operator", "admin"))])
async def get_incidents():
    """All incidents, live ones first if the orchestrator has any, else demo data."""
    coordinator = get_coordinator()
    live = coordinator.list_incidents()
    return live if live else demo_incidents()


@router.get("/incidents/{incident_id}", dependencies=[Depends(require_roles("viewer", "operator", "admin"))])
async def get_incident(incident_id: str):
    coordinator = get_coordinator()
    incident = coordinator.get_incident(incident_id)
    if incident is not None:
        return incident
    for demo in demo_incidents():
        if demo["id"] == incident_id:
            return demo
    raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")


@router.post("/incidents/{incident_id}/approve", dependencies=[Depends(require_roles("operator", "admin"))])
async def approve_incident(incident_id: str):
    coordinator = get_coordinator()
    success = await coordinator.approve_and_execute(incident_id)
    if not success:
        raise HTTPException(
            status_code=409,
            detail="No pending approval found for this incident (it may have expired or already been resolved).",
        )
    return {"success": True}


@router.post("/incidents/{incident_id}/reject", dependencies=[Depends(require_roles("operator", "admin"))])
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


@router.post("/simulate", dependencies=[Depends(require_roles("operator", "admin"))])
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


@router.post("/webhook/incident", dependencies=[Depends(require_roles("operator", "admin"))])
async def inbound_webhook(payload: dict[str, Any]):
    """
    Inbound integration point for external monitoring tools (e.g. Datadog, CloudWatch).
    Expects a JSON payload containing 'service', 'server', and metrics.
    """
    coordinator = get_coordinator()
    server = payload.get("server", "unknown-server")
    service = payload.get("service", "unknown-service")
    
    snapshot = {
        "current_metrics": payload,
        "baseline_metrics": {},
        "recent_log_lines": [f"External webhook trigger received: {payload}"],
    }

    import asyncio
    async def run():
        try:
            await coordinator.run_detection_cycle(
                server=server,
                service=service,
                monitoring_snapshot=snapshot,
            )
        except Exception:
            logger.exception("Webhook incident pipeline failed")

    asyncio.create_task(run())

    return {"success": True, "message": "Webhook accepted, Detective agent dispatched"}


# ── Memory ────────────────────────────────────────────────────────────────────

@router.get("/memory", dependencies=[Depends(require_roles("viewer", "operator", "admin"))])
async def get_memory():
    """Patterns the Memory Agent has learned, for the Memory dashboard page."""
    return demo_memory_records()


def _find_report_payload(report_id: str) -> dict[str, Any] | None:
    for report in demo_reports():
        if report["id"] == report_id or report["incidentId"] == report_id:
            return report

    coordinator = get_coordinator()
    for incident in coordinator.list_incidents():
        report = incident.get("report")
        if not report:
            continue
        candidate_id = report.get("id") or incident.get("id")
        if candidate_id == report_id or incident.get("id") == report_id:
            payload = {**report}
            payload.setdefault("id", f"rpt-{incident.get('id', 'live').lower()}")
            payload.setdefault("incidentId", incident.get("id", "live"))
            payload.setdefault("title", f"{incident.get('title', 'Incident')} — {incident.get('service', 'service')}")
            payload.setdefault(
                "generatedAt",
                report.get("generatedAt") or incident.get("resolvedAt") or datetime.now(timezone.utc).isoformat(),
            )
            payload.setdefault("status", "final")
            payload.setdefault("downtimeMinutes", incident.get("metrics", {}).get("downtimeMinutes", 0))
            return payload
    return None


# ── Reports ───────────────────────────────────────────────────────────────────

@router.get("/reports", dependencies=[Depends(require_roles("viewer", "operator", "admin"))])
async def get_reports():
    return demo_reports()


@router.get("/reports/{report_id}/download", dependencies=[Depends(require_roles("viewer", "operator", "admin"))])
async def download_report(report_id: str):
    """
    Generate a PDF incident report and stream it to the browser.

    If Alibaba Cloud credentials are configured, the same PDF is also uploaded
    to OSS and the public URL is returned in an `X-OSS-URL` response header.
    """
    report = _find_report_payload(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    pdf_bytes = build_report_pdf(report)
    headers = {
        "Content-Disposition": f'inline; filename="{build_report_filename(report)}"',
        "Cache-Control": "no-store",
    }

    try:
        oss_url = await AlibabaCloudService().upload_report(
            key=f"reports/{build_report_filename(report)}",
            content=pdf_bytes,
            content_type="application/pdf",
        )
    except AlibabaCloudNotConfiguredError:
        oss_url = None
    except Exception:
        logger.exception("OSS upload failed for report %s", report_id)
        oss_url = None

    if oss_url:
        headers["X-OSS-URL"] = oss_url

    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
