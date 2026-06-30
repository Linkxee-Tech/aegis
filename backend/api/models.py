"""
Pydantic schemas for the Aegis API.

These are deliberately kept in close lockstep with frontend/src/types/index.ts —
field names and shapes should match exactly so the frontend's mock-data fallback
and the real API are interchangeable from the UI's point of view.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AgentId(str, Enum):
    detective = "detective"
    diagnostician = "diagnostician"
    remediation = "remediation"
    reporter = "reporter"
    memory = "memory"


class AgentStatus(str, Enum):
    active = "active"
    idle = "idle"
    thinking = "thinking"
    error = "error"
    awaiting_approval = "awaiting_approval"


class Agent(BaseModel):
    id: AgentId
    name: str
    role: str
    model: str
    status: AgentStatus
    metric_label: str = Field(alias="metricLabel")
    metric_value: int = Field(alias="metricValue")
    color: str

    class Config:
        populate_by_name = True


class IncidentSeverity(str, Enum):
    critical = "critical"
    warning = "warning"
    info = "info"


class IncidentStatus(str, Enum):
    detected = "detected"
    diagnosing = "diagnosing"
    diagnosed = "diagnosed"
    awaiting_approval = "awaiting_approval"
    remediating = "remediating"
    resolved = "resolved"
    auto_resolved = "auto_resolved"
    rejected = "rejected"


class TimelineEventStatus(str, Enum):
    complete = "complete"
    in_progress = "in_progress"
    pending = "pending"


class TimelineEvent(BaseModel):
    id: str
    agent_id: AgentId = Field(alias="agentId")
    timestamp: str
    title: str
    detail: str
    status: TimelineEventStatus

    class Config:
        populate_by_name = True


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RemediationStep(BaseModel):
    id: str
    order: int
    description: str
    command: str | None = None
    risk_level: RiskLevel = Field(alias="riskLevel")

    class Config:
        populate_by_name = True


class IncidentMetrics(BaseModel):
    cpu_before: float | None = Field(default=None, alias="cpuBefore")
    cpu_after: float | None = Field(default=None, alias="cpuAfter")
    memory_before: float | None = Field(default=None, alias="memoryBefore")
    memory_after: float | None = Field(default=None, alias="memoryAfter")
    downtime_minutes: float | None = Field(default=None, alias="downtimeMinutes")

    class Config:
        populate_by_name = True


class Incident(BaseModel):
    id: str
    title: str
    service: str
    server: str
    severity: IncidentSeverity
    status: IncidentStatus
    detected_at: str = Field(alias="detectedAt")
    resolved_at: str | None = Field(default=None, alias="resolvedAt")
    root_cause: str | None = Field(default=None, alias="rootCause")
    evidence: list[str] = Field(default_factory=list)
    remediation_steps: list[RemediationStep] = Field(default_factory=list, alias="remediationSteps")
    timeline: list[TimelineEvent] = Field(default_factory=list)
    is_auto_resolved: bool = Field(alias="isAutoResolved")
    matched_memory_id: str | None = Field(default=None, alias="matchedMemoryId")
    metrics: IncidentMetrics = Field(default_factory=IncidentMetrics)

    class Config:
        populate_by_name = True


class MemoryRecord(BaseModel):
    id: str
    incident_title: str = Field(alias="incidentTitle")
    root_cause: str = Field(alias="rootCause")
    fix_applied: str = Field(alias="fixApplied")
    occurrences: int
    last_seen: str = Field(alias="lastSeen")
    confidence_score: float = Field(alias="confidenceScore")
    auto_apply_eligible: bool = Field(alias="autoApplyEligible")

    class Config:
        populate_by_name = True


class IncidentReport(BaseModel):
    id: str
    incident_id: str = Field(alias="incidentId")
    title: str
    generated_at: str = Field(alias="generatedAt")
    summary: str
    root_cause_analysis: str = Field(alias="rootCauseAnalysis")
    actions_taken: list[str] = Field(default_factory=list, alias="actionsTaken")
    downtime_minutes: float = Field(alias="downtimeMinutes")
    cost_impact_estimate: str | None = Field(default=None, alias="costImpactEstimate")
    status: str = "draft"

    class Config:
        populate_by_name = True


class SystemHealth(BaseModel):
    all_agents_operational: bool = Field(alias="allAgentsOperational")
    last_incident_ago: str = Field(alias="lastIncidentAgo")
    active_incident_count: int = Field(alias="activeIncidentCount")
    uptime_percentage: float = Field(alias="uptimePercentage")

    class Config:
        populate_by_name = True


class ApprovalRequest(BaseModel):
    incident_id: str = Field(alias="incidentId")
    steps: list[RemediationStep]
    requested_at: str = Field(alias="requestedAt")
    expires_in_seconds: int = Field(alias="expiresInSeconds")

    class Config:
        populate_by_name = True


class RejectionPayload(BaseModel):
    reason: str | None = None


class ApprovalResponse(BaseModel):
    success: bool
    incident_id: str
    new_status: IncidentStatus


class AdminServiceStatus(BaseModel):
    name: str
    status: str
    detail: str


class AdminOverview(BaseModel):
    environment: str
    api_prefix: str = Field(alias="apiPrefix")
    auth_enabled: bool = Field(alias="authEnabled")
    auth_mode: str = Field(alias="authMode")
    backend_status: str = Field(alias="backendStatus")
    startup_ok: bool = Field(alias="startupOk")
    startup_checked_at: str = Field(alias="startupCheckedAt")
    qwen_configured: bool = Field(alias="qwenConfigured")
    database_configured: bool = Field(alias="databaseConfigured")
    redis_configured: bool = Field(alias="redisConfigured")
    monitored_servers: list[str] = Field(alias="monitoredServers")
    agent_count: int = Field(alias="agentCount")
    active_incident_count: int = Field(alias="activeIncidentCount")
    pending_approvals: int = Field(alias="pendingApprovals")
    report_count: int = Field(alias="reportCount")
    memory_record_count: int = Field(alias="memoryRecordCount")
    docs_url: str = Field(alias="docsUrl")
    supported_scenarios: list[str] = Field(alias="supportedScenarios")
    service_matrix: list[AdminServiceStatus] = Field(alias="serviceMatrix")
    recent_signals: list[str] = Field(alias="recentSignals")

    class Config:
        populate_by_name = True


# --- WebSocket event envelope ---

class WsEventType(str, Enum):
    incident_created = "incident_created"
    incident_updated = "incident_updated"
    agent_status_changed = "agent_status_changed"
    timeline_event = "timeline_event"
    approval_required = "approval_required"
    report_generated = "report_generated"


class WsEvent(BaseModel):
    type: WsEventType
    payload: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
