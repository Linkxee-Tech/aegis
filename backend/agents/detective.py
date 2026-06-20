"""
Detective Agent — the first responder.

Watches metric snapshots (CPU, memory, error rate, latency) and recent log lines
against a rolling baseline, and decides whether the deviation is significant
enough to open an incident. Runs on Qwen-Flash because this check happens
continuously and needs to be fast and cheap, not deeply reasoned.
"""

import time
from typing import Any

from backend.agents.base_agent import AgentResult, BaseAgent
from backend.config.prompts import DETECTIVE_SYSTEM_PROMPT
from backend.config.settings import get_settings

settings = get_settings()


class DetectiveAgent(BaseAgent):
    agent_id = "detective"
    model_name = settings.qwen_model_flash
    system_prompt = DETECTIVE_SYSTEM_PROMPT

    async def process(self, context: dict[str, Any]) -> AgentResult:
        """
        context expects:
            server: str
            service: str
            current_metrics: dict (cpu, memory, error_rate, p99_latency_ms)
            baseline_metrics: dict (7-day rolling averages + stddev)
            recent_log_lines: list[str]

        Returns a dict with:
            anomaly_detected: bool
            severity: "critical" | "warning" | "info"
            title: str
            evidence: list[str]
        """
        started_at = time.perf_counter()

        user_prompt = self._build_prompt(context)
        result = await self._call_model(user_prompt, temperature=0.1)

        return self._timed(
            {
                "anomalyDetected": result.get("anomaly_detected", False),
                "severity": result.get("severity", "info"),
                "title": result.get("title", "Unclassified anomaly"),
                "evidence": result.get("evidence", []),
            },
            started_at,
        )

    @staticmethod
    def _build_prompt(context: dict[str, Any]) -> str:
        return f"""Evaluate this monitoring snapshot for {context.get('service')} on {context.get('server')}.

Current metrics: {context.get('current_metrics')}
7-day baseline: {context.get('baseline_metrics')}
Recent log lines (most recent last):
{chr(10).join(context.get('recent_log_lines', []))}

Respond with JSON matching this schema exactly:
{{
  "anomaly_detected": boolean,
  "severity": "critical" | "warning" | "info",
  "title": "short human-readable incident title, e.g. 'CPU Spike on Production Server #3'",
  "evidence": ["specific quantified observation 1", "specific quantified observation 2", ...]
}}"""
