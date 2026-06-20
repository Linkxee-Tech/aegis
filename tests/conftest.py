"""Shared pytest fixtures for unit and integration tests."""

import pytest

from backend.orchestrator.message_bus import MessageBus


@pytest.fixture
def message_bus() -> MessageBus:
    return MessageBus()


@pytest.fixture
def sample_detective_context() -> dict:
    return {
        "server": "prod-ecs-03.ap-southeast-1",
        "service": "payment-service",
        "current_metrics": {"cpu": 97, "memory": 91, "error_rate": 0.18},
        "baseline_metrics": {"cpu_mean": 22, "cpu_std": 6, "memory_mean": 40, "memory_std": 8},
        "recent_log_lines": [
            "2026-06-17T14:31:58Z ERROR payment-service: connection timeout on /v1/charge",
            "2026-06-17T14:32:02Z ERROR payment-service: connection timeout on /v1/charge",
        ],
    }
