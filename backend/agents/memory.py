"""
Memory Agent — the institutional knowledge of Aegis.

Stores every resolved incident's root cause and fix as a vector embedding in
PostgreSQL/pgvector, and on each new incident, searches for the closest past
match. If similarity clears the auto-apply threshold, the orchestrator can
skip the human approval gate and apply the known fix directly — this is the
mechanism behind "next time it remembers."

Runs on Qwen-Plus for the embedding + judgment step (deciding whether a
high-similarity match is *actually* the same root cause, not just superficially
similar symptoms).
"""

import time
from typing import Any

from backend.agents.base_agent import AgentResult, BaseAgent
from backend.config.prompts import MEMORY_SYSTEM_PROMPT
from backend.config.settings import get_settings
from backend.services.memory_store import MemoryStore

settings = get_settings()


class MemoryAgent(BaseAgent):
    agent_id = "memory"
    model_name = settings.qwen_model_plus
    system_prompt = MEMORY_SYSTEM_PROMPT

    def __init__(self, *args: Any, store: MemoryStore | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.store = store or MemoryStore()

    async def process(self, context: dict[str, Any]) -> AgentResult:
        """
        context expects:
            mode: "recall" | "store"
            incident_title: str
            root_cause: str (for recall, may be empty pre-diagnosis)
            fix_applied: list[dict] (for store mode only)

        Returns for "recall":
            match_found: bool
            matched_record: dict | None
            confidence: float
            auto_apply_eligible: bool

        Returns for "store":
            stored: bool
            record_id: str
        """
        started_at = time.perf_counter()
        mode = context.get("mode", "recall")

        if mode == "store":
            data = await self._store(context)
        else:
            data = await self._recall(context)

        return self._timed(data, started_at)

    async def _recall(self, context: dict[str, Any]) -> dict[str, Any]:
        embedding = await self.qwen.embed(
            model="text-embedding-v3",
            text=f"{context.get('incident_title', '')} {context.get('root_cause', '')}",
        )
        candidates = await self.store.search_similar(embedding, top_k=3)

        if not candidates:
            return {"matchFound": False, "matchedRecord": None, "confidence": 0.0, "autoApplyEligible": False}

        best = candidates[0]
        confidence = best["similarity"]
        match_found = confidence >= settings.memory_similarity_threshold
        auto_eligible = confidence >= settings.memory_auto_apply_threshold

        return {
            "matchFound": match_found,
            "matchedRecord": best if match_found else None,
            "confidence": confidence,
            "autoApplyEligible": auto_eligible,
        }

    async def _store(self, context: dict[str, Any]) -> dict[str, Any]:
        embedding = await self.qwen.embed(
            model="text-embedding-v3",
            text=f"{context.get('incident_title', '')} {context.get('root_cause', '')}",
        )
        record_id = await self.store.upsert_record(
            incident_title=context.get("incident_title", ""),
            root_cause=context.get("root_cause", ""),
            fix_applied=context.get("fix_applied", []),
            embedding=embedding,
        )
        return {
            "stored": True,
            "recordId": record_id,
            "message": "Precedence set — this incident pattern and fix are now remembered for future auto-resolution.",
        }
