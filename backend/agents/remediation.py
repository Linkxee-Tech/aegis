"""
Remediation Agent — proposes the fix, executes only after authorization.

Generates a minimal, ordered, risk-tagged sequence of steps to resolve the
diagnosed root cause. Before returning, it validates any bash/Python commands
syntactically so the human approval UI never shows a script with obvious
shell errors. The agent NEVER calls execute_steps() itself — that method is
only invoked by the orchestrator after explicit human approval or an
auto-apply decision.
Runs on Qwen-Coder since steps often include actual commands.
"""

import ast
import logging
import re
import shlex
import subprocess
import time
from typing import Any

from backend.agents.base_agent import AgentResult, BaseAgent
from backend.config.prompts import REMEDIATION_SYSTEM_PROMPT
from backend.config.settings import get_settings
from backend.services.alibaba_cloud import AlibabaCloudService

logger = logging.getLogger("aegis.remediation")
settings = get_settings()


def _validate_command(command: str | None) -> dict[str, Any]:
    """
    Lightweight syntactic validation for generated shell/Python commands.

    Returns a dict with:
        valid: bool
        language: "bash" | "python" | "unknown"
        warning: str | None  — human-readable issue if not valid
    """
    if not command:
        return {"valid": True, "language": "none", "warning": None}

    command = command.strip()

    # --- Python script blocks ---
    if command.startswith("python") or "import " in command or command.startswith("#!/usr/bin/env python"):
        # Extract just the Python code part (strip shebang/python invocation)
        code_match = re.search(r'python3?\s+-c\s+["\'](.+?)["\']', command, re.DOTALL)
        code = code_match.group(1) if code_match else command
        try:
            ast.parse(code)
            return {"valid": True, "language": "python", "warning": None}
        except SyntaxError as e:
            return {"valid": False, "language": "python", "warning": f"Python syntax error: {e}"}

    # --- Bash / shell commands ---
    try:
        # shlex.split catches unclosed quotes and other basic tokenization issues
        shlex.split(command)
    except ValueError as e:
        return {"valid": False, "language": "bash", "warning": f"Shell tokenization error: {e}"}

    # bash -n is a dry-run syntax check (no execution) — use if bash is available
    try:
        result = subprocess.run(
            ["bash", "-n", "-c", command],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode != 0:
            return {
                "valid": False,
                "language": "bash",
                "warning": f"bash -n check failed: {result.stderr.strip()[:200]}",
            }
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # bash not available in this environment — shlex check is sufficient
        pass

    return {"valid": True, "language": "bash", "warning": None}


class RemediationAgent(BaseAgent):
    agent_id = "remediation"
    model_name = settings.qwen_model_coder
    system_prompt = REMEDIATION_SYSTEM_PROMPT

    def __init__(self, *args: Any, cloud_service: AlibabaCloudService | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.cloud_service = cloud_service or AlibabaCloudService()

    async def process(self, context: dict[str, Any]) -> AgentResult:
        """
        context expects:
            root_cause: str
            service: str
            server: str
            matched_memory_confidence: float | None

        Returns a dict with:
            steps: list[{order, description, command, risk_level, validation}]
            requiresHumanApproval: bool
            estimatedDowntimeSeconds: int
            validationWarnings: list[str]
        """
        started_at = time.perf_counter()

        user_prompt = self._build_prompt(context)
        result = await self._call_model(user_prompt, temperature=0.15)

        steps = result.get("steps", [])

        # Validate each command syntactically before proposing to the human.
        # Any invalid command bumps its step to risk_level "high" and flags a
        # warning so the approving engineer can see the concern immediately.
        validation_warnings: list[str] = []
        for step in steps:
            validation = _validate_command(step.get("command"))
            step["validation"] = validation
            if not validation["valid"]:
                warning = f"Step {step.get('order')}: {validation['warning']}"
                validation_warnings.append(warning)
                # Escalate risk so a human definitely reviews it
                step["risk_level"] = "high"
                logger.warning("Remediation step failed syntax validation: %s", warning)

        requires_approval = self._requires_approval(steps, context.get("matched_memory_confidence"))

        return self._timed(
            {
                "steps": steps,
                "requiresHumanApproval": requires_approval,
                "estimatedDowntimeSeconds": result.get("estimated_downtime_seconds", 0),
                "validationWarnings": validation_warnings,
            },
            started_at,
        )

    def _requires_approval(self, steps: list[dict[str, Any]], matched_confidence: float | None) -> bool:
        """A step plan skips human approval only if memory confidence clears the
        auto-apply bar AND no step is high-risk (when that policy is enabled)."""
        has_high_risk_step = any(s.get("risk_level") == "high" for s in steps)
        if settings.require_approval_for_high_risk and has_high_risk_step:
            return True
        if matched_confidence is None:
            return True
        return matched_confidence < settings.memory_auto_apply_threshold

    async def execute_steps(self, *, incident_id: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Execute approved remediation steps against live infrastructure.

        Called ONLY by the orchestrator after approval is granted.
        Never call this from process().
        """
        execution_log: list[dict[str, Any]] = []
        for step in sorted(steps, key=lambda s: s.get("order", 0)):
            outcome = await self.cloud_service.run_remediation_command(
                command=step.get("command", ""),
                description=step.get("description", ""),
            )
            execution_log.append({"step": step.get("order"), "outcome": outcome})
        return {"incidentId": incident_id, "executionLog": execution_log}

    @staticmethod
    def _build_prompt(context: dict[str, Any]) -> str:
        return f"""Propose a remediation plan for this root cause: "{context.get('root_cause')}"

Affected service: {context.get('service')}
Affected server: {context.get('server')}
Matched memory confidence (if any prior solution exists): {context.get('matched_memory_confidence')}

IMPORTANT: Every "command" field must be a syntactically valid bash command or null.
For Python, use: python3 -c "..." with properly escaped quotes.
Prefer well-known CLI tools: kubectl, aliyun, systemctl, docker.

Respond with JSON matching this schema exactly:
{{
  "steps": [
    {{"order": 1, "description": "...", "command": "valid bash/CLI command, or null", "risk_level": "low" | "medium" | "high", "dry_run_output": "simulated text output of command execution"}}
  ],
  "estimated_downtime_seconds": integer
}}"""
