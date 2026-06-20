"""
Integration test exercising the full Detective -> Diagnostician -> Remediation ->
(approval) -> Reporter pipeline, with the Qwen client and infrastructure services
faked out so this runs with no network access and no real Postgres/Redis/Alibaba
Cloud credentials.
"""

import pytest

from backend.agents.detective import DetectiveAgent
from backend.agents.diagnostician import DiagnosticianAgent
from backend.agents.memory import MemoryAgent
from backend.agents.remediation import RemediationAgent
from backend.agents.reporter import ReporterAgent
from backend.orchestrator.coordinator import Coordinator
from backend.orchestrator.message_bus import MessageBus


class FakeQwenClient:
    """Returns canned JSON responses keyed by which agent's system prompt is used."""

    async def complete_json(self, *, model, system_prompt, user_prompt, temperature=0.2, max_tokens=1500):
        if "Detective" in system_prompt:
            return {
                "anomaly_detected": True,
                "severity": "critical",
                "title": "CPU Spike on Production Server #3",
                "evidence": ["CPU climbed from 22% to 97% over 4 minutes"],
            }
        if "Diagnostician" in system_prompt:
            return {
                "root_cause": "Memory leak in payment service after build #4471.",
                "confidence": 0.8,
                "supporting_evidence": ["Heap growth correlates with deploy timestamp"],
                "needs_more_data": False,
            }
        if "Remediation" in system_prompt:
            return {
                "steps": [
                    {"order": 1, "description": "Drain LB pool", "command": "echo drain", "risk_level": "low"},
                    {"order": 2, "description": "Roll back deploy", "command": "echo rollback", "risk_level": "medium"},
                ],
                "estimated_downtime_seconds": 90,
            }
        if "Reporter" in system_prompt:
            return {
                "summary": "Payment service recovered after rollback.",
                "root_cause_analysis": "Memory leak from build #4471.",
                "actions_taken": ["Drained pool", "Rolled back deploy"],
                "cost_impact_estimate": None,
            }
        raise AssertionError(f"Unexpected system prompt in FakeQwenClient: {system_prompt[:50]}")

    async def embed(self, *, model, text):
        return [0.0] * 8


class FakeMemoryStore:
    """No-op memory store — no past incidents, nothing stored, for a clean pipeline run."""

    async def search_similar(self, embedding, *, top_k=3):
        return []

    async def upsert_record(self, *, incident_title, root_cause, fix_applied, embedding):
        return "fake-record-id"


class FakeCloudService:
    async def run_remediation_command(self, *, command, description):
        return {"status": "success", "command": command}


@pytest.fixture
def coordinator() -> Coordinator:
    fake_qwen = FakeQwenClient()
    coord = Coordinator(bus=MessageBus())
    coord.detective = DetectiveAgent(qwen_client=fake_qwen)
    coord.diagnostician = DiagnosticianAgent(qwen_client=fake_qwen)
    coord.remediation = RemediationAgent(qwen_client=fake_qwen, cloud_service=FakeCloudService())
    coord.reporter = ReporterAgent(qwen_client=fake_qwen)
    coord.memory = MemoryAgent(qwen_client=fake_qwen, store=FakeMemoryStore())
    return coord


@pytest.mark.asyncio
async def test_detection_with_no_anomaly_creates_no_incident(coordinator: Coordinator):
    async def quiet_complete_json(**kwargs):
        return {"anomaly_detected": False, "severity": "info", "title": "", "evidence": []}

    # Swap in a detective whose model call reports no anomaly, so we can assert
    # the coordinator correctly short-circuits and never opens an incident.
    coordinator.detective.qwen.complete_json = quiet_complete_json

    incident_id = await coordinator.run_detection_cycle(
        server="prod-ecs-09", service="cache-service", monitoring_snapshot={}
    )
    assert incident_id is None
    assert coordinator.list_incidents() == []


@pytest.mark.asyncio
async def test_full_pipeline_reaches_awaiting_approval(coordinator: Coordinator):
    incident_id = await coordinator.run_detection_cycle(
        server="prod-ecs-03.ap-southeast-1",
        service="payment-service",
        monitoring_snapshot={
            "current_metrics": {"cpu": 97},
            "baseline_metrics": {"cpu_mean": 22},
            "recent_log_lines": ["ERROR timeout"],
            "recent_deploys": [{"build_id": "4471", "deployed_at": "2026-06-17T13:54:00Z"}],
        },
    )

    assert incident_id is not None
    incident = coordinator.get_incident(incident_id)
    assert incident is not None
    assert incident["status"] == "awaiting_approval"
    assert incident["rootCause"] == "Memory leak in payment service after build #4471."
    assert len(incident["remediationSteps"]) == 2
    # Medium-risk step + low confidence (no memory match) -> must wait for a human
    assert incident["isAutoResolved"] is False


@pytest.mark.asyncio
async def test_approval_executes_and_resolves_incident(coordinator: Coordinator):
    incident_id = await coordinator.run_detection_cycle(
        server="prod-ecs-03.ap-southeast-1",
        service="payment-service",
        monitoring_snapshot={"current_metrics": {}, "baseline_metrics": {}, "recent_log_lines": []},
    )
    assert incident_id is not None

    approved = await coordinator.approve_and_execute(incident_id)
    assert approved is True

    incident = coordinator.get_incident(incident_id)
    assert incident["status"] == "resolved"
    assert incident["resolvedAt"] is not None
    assert "report" in incident
    assert incident["report"]["summary"] == "Payment service recovered after rollback."


@pytest.mark.asyncio
async def test_rejecting_remediation_marks_incident_rejected(coordinator: Coordinator):
    incident_id = await coordinator.run_detection_cycle(
        server="prod-ecs-03.ap-southeast-1",
        service="payment-service",
        monitoring_snapshot={"current_metrics": {}, "baseline_metrics": {}, "recent_log_lines": []},
    )
    assert incident_id is not None

    rejected = await coordinator.reject_remediation(incident_id, "Wrong root cause, investigate cache layer instead")
    assert rejected is True
    assert coordinator.get_incident(incident_id)["status"] == "rejected"
