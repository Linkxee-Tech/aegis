"""
Demo data used as a fallback when no live incidents exist yet in the
Coordinator's in-memory store — e.g. right after a fresh deploy, or when
showing the dashboard to judges without first triggering a real detection
cycle.

Deliberately mirrors frontend/src/data/mockData.ts field-for-field so the
dashboard looks identical whether it's reading from this fallback or from a
live backend.
"""

from typing import Any


def demo_agents() -> list[dict[str, Any]]:
    return [
        {
            "id": "detective",
            "name": "Detective",
            "role": "Monitors logs & metrics for anomalies",
            "model": "Qwen-Flash",
            "status": "active",
            "metricLabel": "alerts today",
            "metricValue": 12,
            "color": "detective",
        },
        {
            "id": "diagnostician",
            "name": "Diagnostician",
            "role": "Finds root causes from evidence",
            "model": "Qwen-Plus",
            "status": "active",
            "metricLabel": "analyses run",
            "metricValue": 3,
            "color": "diagnostician",
        },
        {
            "id": "remediation",
            "name": "Remediation",
            "role": "Proposes & executes fixes",
            "model": "Qwen-Coder",
            "status": "awaiting_approval",
            "metricLabel": "actions taken",
            "metricValue": 0,
            "color": "remediation",
        },
        {
            "id": "reporter",
            "name": "Reporter",
            "role": "Documents the full incident",
            "model": "Qwen-Flash",
            "status": "idle",
            "metricLabel": "reports filed",
            "metricValue": 5,
            "color": "reporter",
        },
    ]


def demo_system_health() -> dict[str, Any]:
    return {
        "allAgentsOperational": True,
        "lastIncidentAgo": "2m ago",
        "activeIncidentCount": 1,
        "uptimePercentage": 99.94,
    }


def demo_incidents() -> list[dict[str, Any]]:
    active_incident = {
        "id": "INC-2026-0614",
        "title": "CPU Spike on Production Server #3",
        "service": "payment-service",
        "server": "prod-ecs-03.ap-southeast-1",
        "severity": "critical",
        "status": "awaiting_approval",
        "detectedAt": "2026-06-17T14:32:21Z",
        "resolvedAt": None,
        "evidence": [
            "CPU utilization climbed from 22% to 97% over 4 minutes",
            "Heap memory grew linearly with no GC recovery across 6 sampling windows",
            "14 consecutive timeout errors on /v1/charge endpoint",
            "No corresponding traffic increase in load balancer logs",
        ],
        "rootCause": (
            "A memory leak in the payment service introduced in build #4471 (deployed 38 minutes "
            "before the incident) is retaining transaction objects after the connection pool closes "
            "them, causing the heap to grow until garbage collection can no longer keep pace, "
            "starving the CPU and triggering cascading timeouts."
        ),
        "remediationSteps": [
            {
                "id": "step-1",
                "order": 1,
                "description": "Drain active connections from prod-ecs-03 load balancer pool",
                "command": "aliyun slb DeregisterVirtualServerGroup --VServerGroupId vsg-03 --BackendServers prod-ecs-03",
                "riskLevel": "low",
            },
            {
                "id": "step-2",
                "order": 2,
                "description": "Restart payment-service with previous stable build (#4470)",
                "command": "kubectl rollout undo deployment/payment-service -n prod --to-revision=4470",
                "riskLevel": "medium",
            },
            {
                "id": "step-3",
                "order": 3,
                "description": "Re-register server in load balancer pool and verify health checks",
                "command": "aliyun slb AddVServerGroupBackendServers --VServerGroupId vsg-03 --BackendServers prod-ecs-03",
                "riskLevel": "low",
            },
        ],
        "timeline": [
            {
                "id": "evt-1",
                "agentId": "detective",
                "timestamp": "2026-06-17T14:32:21Z",
                "title": "Anomaly detected",
                "detail": "CPU and memory pattern deviated 4.2 sigma from 7-day baseline on prod-ecs-03.",
                "status": "complete",
            },
            {
                "id": "evt-2",
                "agentId": "diagnostician",
                "timestamp": "2026-06-17T14:33:05Z",
                "title": "Root cause identified",
                "detail": "Correlated heap growth with build #4471 deploy timestamp. Memory leak in connection handling.",
                "status": "complete",
            },
            {
                "id": "evt-3",
                "agentId": "remediation",
                "timestamp": "2026-06-17T14:34:10Z",
                "title": "Fix proposed — awaiting approval",
                "detail": "3-step rollback plan generated. Estimated downtime: 90 seconds.",
                "status": "in_progress",
            },
            {
                "id": "evt-4",
                "agentId": "reporter",
                "timestamp": "",
                "title": "Incident report",
                "detail": "Will generate once remediation completes.",
                "status": "pending",
            },
        ],
        "isAutoResolved": False,
        "matchedMemoryId": None,
        "metrics": {"cpuBefore": 97, "memoryBefore": 91, "downtimeMinutes": None},
    }

    return [
        active_incident,
        {
            "id": "INC-2026-0598",
            "title": "Database connection pool exhaustion",
            "service": "orders-service",
            "server": "prod-ecs-07.ap-southeast-1",
            "severity": "critical",
            "status": "auto_resolved",
            "detectedAt": "2026-06-17T09:14:00Z",
            "resolvedAt": "2026-06-17T09:16:40Z",
            "rootCause": "Connection pool exhausted after a slow downstream inventory query held connections open beyond timeout.",
            "evidence": ["Pool wait time exceeded 5000ms for 230 consecutive requests", "Matched signature of INC-2026-0511"],
            "remediationSteps": [
                {"id": "s1", "order": 1, "description": "Increase pool ceiling temporarily and recycle stale connections", "command": None, "riskLevel": "low"}
            ],
            "timeline": [],
            "isAutoResolved": True,
            "matchedMemoryId": "mem-0511",
            "metrics": {"downtimeMinutes": 2.7},
        },
        {
            "id": "INC-2026-0587",
            "title": "Disk I/O saturation on log volume",
            "service": "logging-agent",
            "server": "prod-ecs-11.ap-southeast-1",
            "severity": "warning",
            "status": "resolved",
            "detectedAt": "2026-06-16T22:03:00Z",
            "resolvedAt": "2026-06-16T22:19:00Z",
            "rootCause": "Verbose debug logging left enabled after a deploy filled the log volume faster than rotation could clear it.",
            "evidence": ["Disk write throughput sustained at 98% capacity for 11 minutes"],
            "remediationSteps": [
                {"id": "s1", "order": 1, "description": "Disable debug logging flag and force log rotation", "command": None, "riskLevel": "low"}
            ],
            "timeline": [],
            "isAutoResolved": False,
            "matchedMemoryId": None,
            "metrics": {"downtimeMinutes": 0},
        },
        {
            "id": "INC-2026-0571",
            "title": "API gateway 5xx surge",
            "service": "api-gateway",
            "server": "prod-ecs-01.ap-southeast-1",
            "severity": "warning",
            "status": "resolved",
            "detectedAt": "2026-06-16T17:48:00Z",
            "resolvedAt": "2026-06-16T18:02:00Z",
            "rootCause": "Upstream auth service certificate rotation caused a brief handshake failure spike.",
            "evidence": ["5xx rate rose to 6.4% for 90 seconds", "TLS handshake errors clustered at auth-service endpoint"],
            "remediationSteps": [
                {"id": "s1", "order": 1, "description": "Force certificate reload on auth-service sidecar", "command": None, "riskLevel": "medium"}
            ],
            "timeline": [],
            "isAutoResolved": False,
            "matchedMemoryId": None,
            "metrics": {"downtimeMinutes": 1.5},
        },
    ]


def demo_memory_records() -> list[dict[str, Any]]:
    return [
        {
            "id": "mem-0511",
            "incidentTitle": "Database connection pool exhaustion",
            "rootCause": "Slow downstream query holding connections beyond timeout",
            "fixApplied": "Temporarily raise pool ceiling and recycle stale connections",
            "occurrences": 4,
            "lastSeen": "2026-06-17T09:14:00Z",
            "confidenceScore": 0.94,
            "autoApplyEligible": True,
        },
        {
            "id": "mem-0398",
            "incidentTitle": "Payment service memory leak after deploy",
            "rootCause": "Unreleased transaction objects after connection pool close",
            "fixApplied": "Roll back to previous stable build, drain & re-register in LB",
            "occurrences": 2,
            "lastSeen": "2026-05-29T03:10:00Z",
            "confidenceScore": 0.81,
            "autoApplyEligible": False,
        },
        {
            "id": "mem-0412",
            "incidentTitle": "Log volume disk saturation",
            "rootCause": "Debug logging left enabled post-deploy",
            "fixApplied": "Disable debug flag, force rotation",
            "occurrences": 6,
            "lastSeen": "2026-06-16T22:03:00Z",
            "confidenceScore": 0.97,
            "autoApplyEligible": True,
        },
        {
            "id": "mem-0290",
            "incidentTitle": "TLS handshake failures on cert rotation",
            "rootCause": "Sidecar caches stale certificate after rotation window",
            "fixApplied": "Force certificate reload on affected sidecar",
            "occurrences": 3,
            "lastSeen": "2026-06-16T17:48:00Z",
            "confidenceScore": 0.88,
            "autoApplyEligible": True,
        },
    ]


def demo_reports() -> list[dict[str, Any]]:
    return [
        {
            "id": "rpt-0598",
            "incidentId": "INC-2026-0598",
            "title": "Database connection pool exhaustion — orders-service",
            "generatedAt": "2026-06-17T09:17:00Z",
            "summary": (
                "A slow downstream inventory query held database connections open past their timeout, "
                "exhausting the orders-service connection pool and causing request failures for 2.7 "
                "minutes. Aegis recognized the pattern from a prior incident and applied the known fix "
                "automatically."
            ),
            "rootCauseAnalysis": (
                "The inventory service introduced a query regression in its latest release that increased "
                "average response time from 40ms to 1.2s under load. Connections held by orders-service "
                "waiting on this query exceeded the pool timeout, and new requests queued until the pool "
                "was exhausted."
            ),
            "actionsTaken": [
                "Detected anomalous pool wait times via Detective Agent",
                "Matched root cause signature against Memory Agent record mem-0511 (94% confidence)",
                "Auto-applied known fix: raised pool ceiling and recycled stale connections",
                "Verified recovery via health check and closed incident without human intervention",
            ],
            "downtimeMinutes": 2.7,
            "costImpactEstimate": "$340 estimated revenue impact avoided vs. manual response",
            "status": "final",
        },
        {
            "id": "rpt-0587",
            "incidentId": "INC-2026-0587",
            "title": "Disk I/O saturation on log volume — logging-agent",
            "generatedAt": "2026-06-16T22:20:00Z",
            "summary": (
                "Debug-level logging left enabled after a routine deploy filled the log volume faster than "
                "rotation could reclaim space, saturating disk I/O for 11 minutes before remediation."
            ),
            "rootCauseAnalysis": (
                "A configuration flag intended for staging was not reset before the production deploy. "
                "This is the sixth recorded occurrence of this pattern."
            ),
            "actionsTaken": [
                "Detective Agent flagged sustained 98% disk write throughput",
                "Diagnostician traced cause to debug flag left active post-deploy",
                "Engineer approved fix: disabled debug logging and forced rotation",
                "Reporter filed incident summary and flagged for deploy-checklist update",
            ],
            "downtimeMinutes": 0,
            "costImpactEstimate": None,
            "status": "final",
        },
    ]
