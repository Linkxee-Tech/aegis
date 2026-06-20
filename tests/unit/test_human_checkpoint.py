import pytest

from backend.orchestrator.human_checkpoint import ApprovalDecision, HumanCheckpoint


class FakeCache:
    """In-memory stand-in for CacheService so these tests don't need Redis."""

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    async def set_pending_approval(self, incident_id: str, payload: dict) -> None:
        self._store[incident_id] = payload

    async def get_pending_approval(self, incident_id: str) -> dict | None:
        return self._store.get(incident_id)

    async def clear_pending_approval(self, incident_id: str) -> None:
        self._store.pop(incident_id, None)


@pytest.fixture
def checkpoint() -> HumanCheckpoint:
    return HumanCheckpoint(cache=FakeCache())


def test_high_risk_step_always_requires_human(checkpoint: HumanCheckpoint):
    steps = [{"order": 1, "risk_level": "high"}]
    decision = checkpoint.evaluate(steps=steps, memory_confidence=0.99, memory_auto_apply_eligible=True)
    assert decision == ApprovalDecision.PENDING_HUMAN


def test_high_confidence_low_risk_auto_approves(checkpoint: HumanCheckpoint):
    steps = [{"order": 1, "risk_level": "low"}]
    decision = checkpoint.evaluate(steps=steps, memory_confidence=0.95, memory_auto_apply_eligible=True)
    assert decision == ApprovalDecision.AUTO_APPROVED


def test_low_confidence_requires_human_even_if_low_risk(checkpoint: HumanCheckpoint):
    steps = [{"order": 1, "risk_level": "low"}]
    decision = checkpoint.evaluate(steps=steps, memory_confidence=0.5, memory_auto_apply_eligible=False)
    assert decision == ApprovalDecision.PENDING_HUMAN


def test_no_memory_match_requires_human(checkpoint: HumanCheckpoint):
    steps = [{"order": 1, "risk_level": "medium"}]
    decision = checkpoint.evaluate(steps=steps, memory_confidence=None, memory_auto_apply_eligible=False)
    assert decision == ApprovalDecision.PENDING_HUMAN


@pytest.mark.asyncio
async def test_approve_returns_false_when_nothing_pending(checkpoint: HumanCheckpoint):
    result = await checkpoint.approve(incident_id="INC-DOES-NOT-EXIST")
    assert result is False


@pytest.mark.asyncio
async def test_approve_succeeds_for_a_pending_request(checkpoint: HumanCheckpoint):
    await checkpoint.request_approval(incident_id="INC-1", steps=[{"order": 1, "risk_level": "low"}])
    result = await checkpoint.approve(incident_id="INC-1")
    assert result is True

    # Second approval attempt should fail — it was already cleared.
    second = await checkpoint.approve(incident_id="INC-1")
    assert second is False


@pytest.mark.asyncio
async def test_reject_clears_pending_request(checkpoint: HumanCheckpoint):
    await checkpoint.request_approval(incident_id="INC-2", steps=[{"order": 1, "risk_level": "low"}])
    result = await checkpoint.reject(incident_id="INC-2", reason="Wrong root cause")
    assert result is True
