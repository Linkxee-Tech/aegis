"""
Human Approval Checkpoint — the gate between a proposed fix and a live action.

This module owns the decision of whether a remediation plan may proceed
automatically or must wait for an engineer to click Approve. It is deliberately
the only place in the codebase that makes that decision, so the policy is easy
to audit and change in one spot.
"""

import logging
import time
from typing import Any

from backend.config.settings import get_settings
from backend.services.cache import CacheService, get_cache

logger = logging.getLogger("aegis.human_checkpoint")
settings = get_settings()


class ApprovalDecision:
    AUTO_APPROVED = "auto_approved"
    PENDING_HUMAN = "pending_human"


class HumanCheckpoint:
    """Decides whether a remediation plan needs a human, and tracks pending approvals."""

    def __init__(self, cache: CacheService | None = None) -> None:
        self.cache = cache or get_cache()

    def evaluate(
        self,
        *,
        steps: list[dict[str, Any]],
        memory_confidence: float | None,
        memory_auto_apply_eligible: bool,
    ) -> str:
        """
        Returns ApprovalDecision.AUTO_APPROVED if the plan may run immediately,
        or ApprovalDecision.PENDING_HUMAN if it must wait for explicit sign-off.

        Policy, in order:
          1. Any high-risk step always requires a human, if that policy flag is on
             — regardless of how confident the Memory Agent is.
          2. Otherwise, a sufficiently confident memory match (>= auto_apply
             threshold) is allowed to proceed automatically.
          3. Anything else waits for a human.
        """
        has_high_risk = any(s.get("risk_level") == "high" or s.get("riskLevel") == "high" for s in steps)
        if settings.require_approval_for_high_risk and has_high_risk:
            return ApprovalDecision.PENDING_HUMAN

        if memory_auto_apply_eligible and memory_confidence is not None:
            if memory_confidence >= settings.memory_auto_apply_threshold:
                return ApprovalDecision.AUTO_APPROVED

        return ApprovalDecision.PENDING_HUMAN

    async def request_approval(self, *, incident_id: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
        """Records a pending approval request with a TTL so it expires if ignored."""
        payload = {
            "incidentId": incident_id,
            "steps": steps,
            "requestedAt": time.time(),
            "expiresInSeconds": settings.approval_timeout_seconds,
        }
        await self.cache.set_pending_approval(incident_id, payload)
        logger.info("Approval requested for incident %s (%d steps)", incident_id, len(steps))
        return payload

    async def approve(self, *, incident_id: str) -> bool:
        """Marks a pending approval as granted. Returns False if no pending request exists (e.g. expired)."""
        pending = await self.cache.get_pending_approval(incident_id)
        if pending is None:
            logger.warning("Approval attempted for incident %s with no pending request (expired?)", incident_id)
            return False
        await self.cache.clear_pending_approval(incident_id)
        return True

    async def reject(self, *, incident_id: str, reason: str | None) -> bool:
        pending = await self.cache.get_pending_approval(incident_id)
        if pending is None:
            return False
        await self.cache.clear_pending_approval(incident_id)
        logger.info("Approval rejected for incident %s. Reason: %s", incident_id, reason or "(none given)")
        return True
