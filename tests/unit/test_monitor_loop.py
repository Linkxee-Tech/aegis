import pytest

from backend.orchestrator.monitor_loop import MonitorLoop


class StubCoordinator:
    """MonitorLoop only needs run_detection_cycle from the coordinator for these tests."""

    async def run_detection_cycle(self, **kwargs):
        return None


@pytest.fixture
def loop() -> MonitorLoop:
    return MonitorLoop(coordinator=StubCoordinator())


def test_first_sample_has_no_baseline_yet(loop: MonitorLoop):
    baseline = loop._update_and_get_baseline("server-a", {"cpu": 50.0})
    # No prior history exists yet, so there's nothing to compute a mean/std from.
    assert baseline == {}


def test_baseline_computed_after_multiple_samples(loop: MonitorLoop):
    loop._update_and_get_baseline("server-a", {"cpu": 20.0})
    loop._update_and_get_baseline("server-a", {"cpu": 22.0})
    baseline = loop._update_and_get_baseline("server-a", {"cpu": 24.0})

    assert baseline["cpu_mean"] == pytest.approx(21.0, rel=1e-3)
    assert baseline["cpu_std"] > 0


def test_baselines_are_isolated_per_server(loop: MonitorLoop):
    loop._update_and_get_baseline("server-a", {"cpu": 90.0})
    loop._update_and_get_baseline("server-a", {"cpu": 90.0})
    baseline_b = loop._update_and_get_baseline("server-b", {"cpu": 10.0})

    # server-b has no history of its own yet, so it must not inherit server-a's data.
    assert baseline_b == {}


def test_baseline_window_caps_at_max_size(loop: MonitorLoop):
    from backend.orchestrator.monitor_loop import BASELINE_WINDOW_SIZE

    for i in range(BASELINE_WINDOW_SIZE + 10):
        loop._update_and_get_baseline("server-a", {"cpu": float(i)})

    history = loop._baselines["server-a"]["cpu"]
    assert len(history) == BASELINE_WINDOW_SIZE
