"""
Reporter Agent — closes the loop with documentation.

Takes the full incident lifecycle and produces a structured Markdown incident
report suitable for an audit log, management summary, or PDF export.
Runs on Qwen-Flash since this is summarization of already-gathered facts.
"""

import time
from typing import Any

from backend.agents.base_agent import AgentResult, BaseAgent
from backend.config.prompts import REPORTER_SYSTEM_PROMPT
from backend.config.settings import get_settings

settings = get_settings()


class ReporterAgent(BaseAgent):
    agent_id = "reporter"
    model_name = settings.qwen_model_flash
    system_prompt = REPORTER_SYSTEM_PROMPT

    async def process(self, context: dict[str, Any]) -> AgentResult:
        """
        context expects:
            incident: dict  -- full incident record including timeline
            downtime_minutes: float

        Returns a dict with:
            summary: str
            rootCauseAnalysis: str
            actionsTaken: list[str]
            costImpactEstimate: str | None
            markdownReport: str  -- full Markdown document for export/display
        """
        started_at = time.perf_counter()

        user_prompt = self._build_prompt(context)
        result = await self._call_model(user_prompt, temperature=0.3)

        incident = context.get("incident", {})
        downtime = context.get("downtime_minutes", 0)
        actions = result.get("actions_taken", [])
        markdown = self._build_markdown(incident, result, downtime, actions)

        return self._timed(
            {
                "summary": result.get("summary", ""),
                "rootCauseAnalysis": result.get("root_cause_analysis", ""),
                "actionsTaken": actions,
                "costImpactEstimate": result.get("cost_impact_estimate"),
                "markdownReport": markdown,
            },
            started_at,
        )

    @staticmethod
    def _build_markdown(
        incident: dict[str, Any],
        result: dict[str, Any],
        downtime_minutes: float,
        actions: list[str],
    ) -> str:
        """Assembles the full Markdown incident report document."""
        severity = incident.get("severity", "unknown").upper()
        status = incident.get("status", "unknown").replace("_", " ").title()
        lines = [
            f"# Incident Report — {incident.get('title', 'Untitled')}",
            "",
            f"**Incident ID:** `{incident.get('id', 'N/A')}`  ",
            f"**Severity:** {severity}  ",
            f"**Status:** {status}  ",
            f"**Service / Server:** `{incident.get('service', 'N/A')}` / `{incident.get('server', 'N/A')}`  ",
            f"**Detected:** {incident.get('detectedAt', 'N/A')}  ",
            f"**Resolved:** {incident.get('resolvedAt', 'N/A')}  ",
            f"**Downtime:** {downtime_minutes} minutes  ",
            f"**Auto-resolved:** {'Yes' if incident.get('isAutoResolved') else 'No'}  ",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            result.get("summary", ""),
            "",
            "## Root Cause Analysis",
            "",
            result.get("root_cause_analysis", ""),
            "",
            "## Evidence",
            "",
        ]
        for ev in incident.get("evidence", []):
            lines.append(f"- {ev}")
        lines += ["", "## Remediation Steps Taken", ""]
        for i, action in enumerate(actions, 1):
            lines.append(f"{i}. {action}")
        cost = result.get("cost_impact_estimate")
        if cost:
            lines += ["", "## Cost Impact", "", cost]
        lines += ["", "## Timeline", "", "| Time | Agent | Event |", "|---|---|---|"]
        for event in incident.get("timeline", []):
            ts = event.get("timestamp", "")[:19].replace("T", " ")
            agent = event.get("agentId", "").capitalize()
            title = event.get("title", "")
            lines.append(f"| {ts} | {agent} | {title} |")
        lines += ["", "---", "", "_Generated automatically by Aegis Reporter Agent_"]
        return "\n".join(lines)

    @staticmethod
    def _build_prompt(context: dict[str, Any]) -> str:
        incident = context.get("incident", {})
        return f"""Write a concise incident report for the following resolved incident.

Title: {incident.get('title')}
Service / server: {incident.get('service')} / {incident.get('server')}
Root cause: {incident.get('rootCause')}
Remediation steps taken: {incident.get('remediationSteps')}
Was this auto-resolved from memory: {incident.get('isAutoResolved')}
Downtime: {context.get('downtime_minutes')} minutes

Respond with JSON matching this schema exactly:
{{
  "summary": "2-3 sentence executive summary, leading with impact and outcome",
  "root_cause_analysis": "clear explanation of why this happened",
  "actions_taken": ["action 1 in past tense", "action 2 in past tense"],
  "cost_impact_estimate": "short estimate string, or null if not estimable"
}}"""
