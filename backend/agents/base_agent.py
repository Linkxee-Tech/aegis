"""
Abstract base class that every Aegis agent extends.

The contract is intentionally small: an agent receives a context dict, does
whatever model calls and tool calls it needs, and returns a structured result
dict. Orchestration, retries, and message-bus plumbing live outside the agent —
agents stay focused on "given this evidence, produce this judgment."
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from backend.services.qwen_client import QwenClient, get_qwen_client

logger = logging.getLogger("aegis.agents")


class AgentResult:
    """Wraps an agent's output along with timing and confidence metadata."""

    def __init__(self, data: dict[str, Any], *, duration_ms: float, agent_id: str) -> None:
        self.data = data
        self.duration_ms = duration_ms
        self.agent_id = agent_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "agentId": self.agent_id,
            "durationMs": round(self.duration_ms, 1),
            **self.data,
        }


class BaseAgent(ABC):
    """
    Extend this class to add a new agent to Aegis.

    Subclasses must set `agent_id`, `model_name`, and `system_prompt`, and
    implement `process()`. Use `self._call_model(...)` to talk to Qwen Cloud —
    it handles timing and logging consistently across agents.
    """

    agent_id: str
    model_name: str
    system_prompt: str

    def __init__(self, qwen_client: QwenClient | None = None) -> None:
        self.qwen = qwen_client or get_qwen_client()

    @abstractmethod
    async def process(self, context: dict[str, Any]) -> AgentResult:
        """
        Run this agent against the given context and return a structured result.

        `context` shape varies by agent — see each subclass's docstring — but
        every agent should treat it as read-only input and return new data
        rather than mutating the incident object directly. The orchestrator
        is responsible for merging results into incident state.
        """
        raise NotImplementedError

    async def _call_model(self, user_prompt: str, *, temperature: float = 0.2) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            result = await self.qwen.complete_json(
                model=self.model_name,
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
            )
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info("%s call took %.1fms", self.agent_id, elapsed_ms)
        return result

    def _timed(self, data: dict[str, Any], started_at: float) -> AgentResult:
        duration_ms = (time.perf_counter() - started_at) * 1000
        return AgentResult(data, duration_ms=duration_ms, agent_id=self.agent_id)
