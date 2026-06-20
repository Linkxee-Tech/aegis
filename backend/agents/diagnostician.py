"""
Diagnostician Agent — figures out why, not just what.

Takes the Detective's alert plus deeper context (recent deploys, related past
incidents from the Memory Agent, broader log windows) and produces a root-cause
hypothesis with supporting evidence. Runs on Qwen-Plus since this step benefits
from stronger reasoning more than the constant-polling Detective does.
"""

import time
from typing import Any

from backend.agents.base_agent import AgentResult, BaseAgent
from backend.config.prompts import DIAGNOSTICIAN_SYSTEM_PROMPT
from backend.config.settings import get_settings

settings = get_settings()


class DiagnosticianAgent(BaseAgent):
    agent_id = "diagnostician"
    model_name = settings.qwen_model_plus
    system_prompt = DIAGNOSTICIAN_SYSTEM_PROMPT

    async def process(self, context: dict[str, Any]) -> AgentResult:
        """
        context expects:
            incident_title: str
            evidence: list[str]
            extended_logs: list[str]
            recent_deploys: list[dict]  # [{build_id, deployed_at, service}, ...]
            similar_past_incidents: list[dict]  # from Memory Agent

        Returns a dict with:
            root_cause: str
            confidence: float (0-1)
            supporting_evidence: list[str]
            needs_more_data: bool
        """
        started_at = time.perf_counter()

        user_prompt = self._build_prompt(context)
        result = await self._call_model(user_prompt, temperature=0.2)

        return self._timed(
            {
                "rootCause": result.get("root_cause", ""),
                "confidence": result.get("confidence", 0.0),
                "supportingEvidence": result.get("supporting_evidence", []),
                "needsMoreData": result.get("needs_more_data", False),
            },
            started_at,
        )

    @staticmethod
    def _build_prompt(context: dict[str, Any]) -> str:
        return f"""Diagnose the root cause of this incident: "{context.get('incident_title')}"

Detective's evidence:
{chr(10).join(context.get('evidence', []))}

Extended log context:
{chr(10).join(context.get('extended_logs', []))}

Recent deploys to this service: {context.get('recent_deploys', [])}

Similar past incidents from memory: {context.get('similar_past_incidents', [])}

Respond with JSON matching this schema exactly:
{{
  "root_cause": "one or two sentence explanation of why this happened",
  "confidence": float between 0 and 1,
  "supporting_evidence": ["evidence point that supports this conclusion", ...],
  "needs_more_data": boolean
}}"""
