"""
Startup health verification for Aegis.

This module performs the lightweight checks we can validate locally at boot:
- agent modules import and instantiate
- required agent IDs are present
- core service settings are readable

The check is intentionally non-networked so development startup stays fast and
does not fail just because Qwen or cloud infrastructure is temporarily absent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

from backend.config.settings import get_settings


@dataclass(slots=True)
class StartupCheckResult:
    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


AGENT_IMPORTS = (
    ("detective", "backend.agents.detective", "DetectiveAgent"),
    ("diagnostician", "backend.agents.diagnostician", "DiagnosticianAgent"),
    ("remediation", "backend.agents.remediation", "RemediationAgent"),
    ("reporter", "backend.agents.reporter", "ReporterAgent"),
    ("memory", "backend.agents.memory", "MemoryAgent"),
)


async def run_startup_health_check() -> dict[str, Any]:
    settings = get_settings()
    checks: list[StartupCheckResult] = []
    healthy = True
    agent_ids: list[str] = []

    for expected_id, module_path, class_name in AGENT_IMPORTS:
        try:
            module = import_module(module_path)
            agent_cls = getattr(module, class_name)
            agent = agent_cls()
            actual_id = getattr(agent, "agent_id", "")
            agent_ids.append(actual_id)
            if actual_id != expected_id:
                healthy = False
                checks.append(
                    StartupCheckResult(
                        name=expected_id,
                        ok=False,
                        detail=f"Expected agent_id '{expected_id}', got '{actual_id or 'missing'}'",
                    )
                )
            else:
                checks.append(
                    StartupCheckResult(
                        name=expected_id,
                        ok=True,
                        detail=f"Imported {class_name} from {module_path}",
                    )
                )
        except Exception as exc:
            healthy = False
            checks.append(
                StartupCheckResult(
                    name=expected_id,
                    ok=False,
                    detail=f"{module_path}.{class_name} failed to load: {exc}",
                )
            )

    if len(agent_ids) != len(set(agent_ids)):
        healthy = False
        checks.append(
            StartupCheckResult(
                name="agent_id_uniqueness",
                ok=False,
                detail="One or more agent IDs are duplicated",
            )
        )
    else:
        checks.append(
            StartupCheckResult(
                name="agent_id_uniqueness",
                ok=True,
                detail="All agent IDs are unique",
            )
        )

    checks.append(
        StartupCheckResult(
            name="qwen_configuration",
            ok=bool(settings.qwen_api_key),
            detail="Qwen API key configured" if settings.qwen_api_key else "Qwen API key missing; demo mode will continue",
        )
    )

    return {
        "ok": healthy,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "checks": [check.to_dict() for check in checks],
    }
