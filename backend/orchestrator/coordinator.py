"""
Coordinator — runs the full Detective -> Diagnostician -> Remediation -> Reporter
pipeline for an incident, consulting the Memory Agent at two points (recall before
remediation, store after resolution) and the HumanCheckpoint before any live action.

This is the one place that knows the *shape* of the whole workflow. Each agent
stays ignorant of the others; the Coordinator is what makes them a team.
"""

import logging
import time
import uuid
import httpx
from datetime import datetime, timezone
from typing import Any

from backend.config.settings import get_settings

from backend.agents.detective import DetectiveAgent
from backend.agents.diagnostician import DiagnosticianAgent
from backend.agents.memory import MemoryAgent
from backend.agents.remediation import RemediationAgent
from backend.agents.reporter import ReporterAgent
from backend.orchestrator.human_checkpoint import ApprovalDecision, HumanCheckpoint
from backend.orchestrator.message_bus import (
    TOPIC_AGENT_STATUS_CHANGED,
    TOPIC_APPROVAL_REQUIRED,
    TOPIC_INCIDENT_CREATED,
    TOPIC_INCIDENT_UPDATED,
    TOPIC_REPORT_GENERATED,
    TOPIC_TIMELINE_EVENT,
    MessageBus,
    get_message_bus,
)

logger = logging.getLogger("aegis.coordinator")


class Coordinator:
    """
    Owns the in-memory incident store and drives the multi-agent pipeline.

    In this reference implementation incidents live in memory (`self._incidents`)
    for simplicity; a production deployment would back this with the same
    PostgreSQL instance the Memory Agent uses, keyed by incident id, so state
    survives a restart. The pipeline logic itself doesn't change either way.
    """

    def __init__(self, bus: MessageBus | None = None) -> None:
        self.bus = bus or get_message_bus()
        self.detective = DetectiveAgent()
        self.diagnostician = DiagnosticianAgent()
        self.remediation = RemediationAgent()
        self.reporter = ReporterAgent()
        self.memory = MemoryAgent()
        self.checkpoint = HumanCheckpoint()
        self._incidents: dict[str, dict[str, Any]] = {}

    # --- public incident store accessors, used by the API layer ---

    def list_incidents(self) -> list[dict[str, Any]]:
        return list(self._incidents.values())

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        return self._incidents.get(incident_id)

    # --- pipeline ---

    async def run_detection_cycle(self, *, server: str, service: str, monitoring_snapshot: dict[str, Any]) -> str | None:
        """
        Entry point for a single Detective poll. Returns the new incident id if
        an anomaly was confirmed, else None. On a hit, kicks off the rest of the
        pipeline as a background continuation.
        """
        await self._publish_agent_status("detective", "thinking")
        result = await self.detective.process(
            {
                "server": server,
                "service": service,
                "current_metrics": monitoring_snapshot.get("current_metrics", {}),
                "baseline_metrics": monitoring_snapshot.get("baseline_metrics", {}),
                "recent_log_lines": monitoring_snapshot.get("recent_log_lines", []),
            }
        )
        await self._publish_agent_status("detective", "active")

        if not result.data.get("anomalyDetected"):
            return None

        incident_id = self._new_incident_id()
        incident = self._create_incident_record(
            incident_id=incident_id,
            server=server,
            service=service,
            detective_result=result.data,
        )
        self._incidents[incident_id] = incident

        await self.bus.publish(TOPIC_INCIDENT_CREATED, incident)
        await self._emit_timeline_event(
            incident_id,
            agent_id="detective",
            title="Anomaly detected",
            detail="; ".join(result.data.get("evidence", []))[:300],
        )

        await self._continue_pipeline(incident_id, monitoring_snapshot)
        return incident_id

    async def _continue_pipeline(self, incident_id: str, monitoring_snapshot: dict[str, Any]) -> None:
        incident = self._incidents[incident_id]

        # --- Memory recall, before diagnosis, to give the Diagnostician context ---
        await self._publish_agent_status("memory", "active")
        recall = await self.memory.process(
            {"mode": "recall", "incident_title": incident["title"], "root_cause": ""}
        )
        await self._publish_agent_status("memory", "idle")
        similar_past_incidents = [recall.data["matchedRecord"]] if recall.data.get("matchFound") else []

        # --- Diagnostician ---
        incident["status"] = "diagnosing"
        await self.bus.publish(TOPIC_INCIDENT_UPDATED, incident)
        await self._publish_agent_status("diagnostician", "thinking")
        diagnosis = await self.diagnostician.process(
            {
                "incident_title": incident["title"],
                "evidence": incident["evidence"],
                "extended_logs": monitoring_snapshot.get("recent_log_lines", []),
                "recent_deploys": monitoring_snapshot.get("recent_deploys", []),
                "similar_past_incidents": similar_past_incidents,
            }
        )
        await self._publish_agent_status("diagnostician", "active")

        incident["rootCause"] = diagnosis.data["rootCause"]
        incident["status"] = "diagnosed"
        await self._emit_timeline_event(
            incident_id,
            agent_id="diagnostician",
            title="Root cause identified",
            detail=diagnosis.data["rootCause"],
        )

        # --- Memory recall again, now with the real root cause, for accurate matching ---
        recall = await self.memory.process(
            {"mode": "recall", "incident_title": incident["title"], "root_cause": diagnosis.data["rootCause"]}
        )
        matched_confidence = recall.data.get("confidence")
        auto_eligible = recall.data.get("autoApplyEligible", False)
        if recall.data.get("matchFound"):
            incident["matchedMemoryId"] = recall.data["matchedRecord"]["id"]

        # --- Remediation proposal ---
        await self._publish_agent_status("remediation", "thinking")
        remediation = await self.remediation.process(
            {
                "root_cause": diagnosis.data["rootCause"],
                "service": incident["service"],
                "server": incident["server"],
                "matched_memory_confidence": matched_confidence,
            }
        )
        steps = remediation.data["steps"]
        incident["remediationSteps"] = steps

        decision = self.checkpoint.evaluate(
            steps=steps,
            memory_confidence=matched_confidence,
            memory_auto_apply_eligible=auto_eligible,
        )

        if decision == ApprovalDecision.AUTO_APPROVED:
            await self._publish_agent_status("remediation", "active")
            incident["status"] = "remediating"
            incident["isAutoResolved"] = True
            await self._emit_timeline_event(
                incident_id,
                agent_id="remediation",
                title="Fix auto-applied from memory",
                detail=f"Matched prior incident with {matched_confidence:.0%} confidence — executing without human approval.",
            )
            await self.remediation.execute_steps(incident_id=incident_id, steps=steps)
            await self._resolve_incident(incident_id)
        else:
            await self._publish_agent_status("remediation", "awaiting_approval")
            incident["status"] = "awaiting_approval"
            await self._emit_timeline_event(
                incident_id,
                agent_id="remediation",
                title="Fix proposed — awaiting approval",
                detail=f"{len(steps)}-step plan generated. Estimated downtime: {remediation.data.get('estimatedDowntimeSeconds', 0)}s.",
            )
            await self.checkpoint.request_approval(incident_id=incident_id, steps=steps)
            await self.bus.publish(TOPIC_APPROVAL_REQUIRED, {"incidentId": incident_id, "steps": steps})

        await self.bus.publish(TOPIC_INCIDENT_UPDATED, incident)

    async def approve_and_execute(self, incident_id: str) -> bool:
        """Called by the API layer when an engineer clicks Approve."""
        incident = self._incidents.get(incident_id)
        if incident is None:
            return False

        approved = await self.checkpoint.approve(incident_id=incident_id)
        if not approved:
            return False

        await self._publish_agent_status("remediation", "active")
        incident["status"] = "remediating"
        await self._emit_timeline_event(
            incident_id, agent_id="remediation", title="Fix approved & executed", detail="Engineer approved the proposed plan."
        )
        await self.remediation.execute_steps(incident_id=incident_id, steps=incident["remediationSteps"])
        await self._resolve_incident(incident_id)
        return True

    async def reject_remediation(self, incident_id: str, reason: str | None) -> bool:
        incident = self._incidents.get(incident_id)
        if incident is None:
            return False
        rejected = await self.checkpoint.reject(incident_id=incident_id, reason=reason)
        if rejected:
            incident["status"] = "rejected"
            await self._emit_timeline_event(
                incident_id,
                agent_id="remediation",
                title="Fix rejected",
                detail=reason or "Rejected by engineer with no reason given.",
            )
            await self.bus.publish(TOPIC_INCIDENT_UPDATED, incident)
        return rejected

    async def _resolve_incident(self, incident_id: str) -> None:
        incident = self._incidents[incident_id]
        incident["status"] = "auto_resolved" if incident.get("isAutoResolved") else "resolved"
        incident["resolvedAt"] = datetime.now(timezone.utc).isoformat()

        downtime_minutes = self._estimate_downtime_minutes(incident)
        incident["metrics"]["downtimeMinutes"] = downtime_minutes

        # --- Memory store, so the next occurrence is recognized ---
        await self._publish_agent_status("memory", "active")
        memory_store_result = await self.memory.process(
            {
                "mode": "store",
                "incident_title": incident["title"],
                "root_cause": incident["rootCause"],
                "fix_applied": incident["remediationSteps"],
            }
        )
        await self._publish_agent_status("memory", "idle")
        await self._emit_timeline_event(
            incident_id,
            agent_id="memory",
            title="Memory updated",
            detail=memory_store_result.data.get(
                "message",
                "Precedence set — this incident pattern and fix are now remembered for future auto-resolution."
            ),
        )

        # --- Reporter ---
        await self._publish_agent_status("reporter", "thinking")
        report = await self.reporter.process({"incident": incident, "downtime_minutes": downtime_minutes})
        await self._publish_agent_status("reporter", "active")
        report_data = {
            **report.data,
            "id": f"rpt-{incident_id.lower()}",
            "incidentId": incident_id,
            "title": f"{incident['title']} — {incident['service']}",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "status": "final",
            "downtimeMinutes": downtime_minutes,
        }
        incident["report"] = report_data
        await self._emit_timeline_event(
            incident_id, agent_id="reporter", title="Incident report generated", detail=report.data["summary"]
        )
        await self.bus.publish(TOPIC_REPORT_GENERATED, {"incidentId": incident_id, "report": report_data})
        await self.bus.publish(TOPIC_INCIDENT_UPDATED, incident)
        await self._publish_agent_status("reporter", "idle")

        # --- Outbound Webhook (Slack) ---
        settings = get_settings()
        if settings.slack_webhook_url:
            try:
                slack_payload = {
                    "text": f"✅ *Incident {incident_id} Resolved*\n*Service*: {incident['service']}\n*Root Cause*: {incident['rootCause']}\n*Downtime*: {downtime_minutes} mins\n_Aegis automatically tracked and generated a report for this event._"
                }
                async with httpx.AsyncClient() as client:
                    await client.post(settings.slack_webhook_url, json=slack_payload, timeout=5.0)
            except Exception:
                logger.exception(f"Failed to push Slack webhook for {incident_id}")

    # --- helpers ---

    def _new_incident_id(self) -> str:
        now = datetime.now(timezone.utc)
        return f"INC-{now.year}-{uuid.uuid4().hex[:4].upper()}"

    def _create_incident_record(
        self, *, incident_id: str, server: str, service: str, detective_result: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "id": incident_id,
            "title": detective_result.get("title", "Unclassified anomaly"),
            "service": service,
            "server": server,
            "severity": detective_result.get("severity", "warning"),
            "status": "detected",
            "detectedAt": datetime.now(timezone.utc).isoformat(),
            "resolvedAt": None,
            "rootCause": None,
            "evidence": detective_result.get("evidence", []),
            "remediationSteps": [],
            "timeline": [],
            "isAutoResolved": False,
            "matchedMemoryId": None,
            "metrics": {},
        }

    async def _emit_timeline_event(self, incident_id: str, *, agent_id: str, title: str, detail: str) -> None:
        event = {
            "id": uuid.uuid4().hex[:8],
            "agentId": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "title": title,
            "detail": detail,
            "status": "complete",
        }
        self._incidents[incident_id]["timeline"].append(event)
        await self.bus.publish(TOPIC_TIMELINE_EVENT, {"incidentId": incident_id, "event": event})

    async def _publish_agent_status(self, agent_id: str, status: str) -> None:
        await self.bus.publish(TOPIC_AGENT_STATUS_CHANGED, {"agentId": agent_id, "status": status})

    @staticmethod
    def _estimate_downtime_minutes(incident: dict[str, Any]) -> float:
        if not incident.get("detectedAt") or not incident.get("resolvedAt"):
            return 0.0
        start = datetime.fromisoformat(incident["detectedAt"])
        end = datetime.fromisoformat(incident["resolvedAt"])
        return round((end - start).total_seconds() / 60, 1)


_coordinator: Coordinator | None = None


def get_coordinator() -> Coordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = Coordinator()
    return _coordinator
