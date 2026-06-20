"""
Background monitoring loop — the piece that actually makes the Detective Agent
"constantly monitor" something, rather than only responding to manual or
test-driven calls to Coordinator.run_detection_cycle().

Runs as an asyncio background task started from main.py's startup event. For
each server in settings.monitored_servers, on a settings.poll_interval_seconds
cadence, it:
  1. Pulls current metrics via AlibabaCloudService.fetch_instance_metrics
  2. Maintains a simple rolling baseline in memory
  3. Hands both to Coordinator.run_detection_cycle, which is where the actual
     Detective Agent model call and the rest of the pipeline happen

If Alibaba Cloud credentials aren't configured (e.g. a local dev/demo
environment), `fetch_instance_metrics` raises `AlibabaCloudNotConfiguredError`
on the first attempt — this loop logs that once per server and then stops
polling that server, rather than retrying forever or crashing the app.
"""

import asyncio
import logging
from collections import deque
from typing import Deque

from backend.config.settings import get_settings
from backend.orchestrator.coordinator import Coordinator
from backend.services.alibaba_cloud import AlibabaCloudNotConfiguredError, AlibabaCloudService

logger = logging.getLogger("aegis.monitor")
settings = get_settings()

BASELINE_WINDOW_SIZE = 50  # number of recent samples kept per metric, per server


class MonitorLoop:
    """Owns one polling task per monitored server."""

    def __init__(self, coordinator: Coordinator, cloud_service: AlibabaCloudService | None = None) -> None:
        self.coordinator = coordinator
        self.cloud_service = cloud_service or AlibabaCloudService()
        self._tasks: list[asyncio.Task] = []
        self._baselines: dict[str, dict[str, Deque[float]]] = {}
        self._stopped = False

    def start(self) -> None:
        if not settings.monitored_servers:
            logger.info("MONITORED_SERVERS is empty — background monitoring is idle. "
                        "Set it in .env to start watching real instances.")
            return
        for server in settings.monitored_servers:
            task = asyncio.create_task(self._poll_server(server), name=f"monitor:{server}")
            self._tasks.append(task)
        logger.info("Started monitoring %d server(s) every %ds", len(settings.monitored_servers), settings.poll_interval_seconds)

    async def stop(self) -> None:
        self._stopped = True
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _poll_server(self, server: str) -> None:
        service = server.split(".")[0]  # best-effort service name from the instance hostname
        while not self._stopped:
            try:
                metrics = await self.cloud_service.fetch_instance_metrics(instance_id=server)
                baseline = self._update_and_get_baseline(server, metrics)
                await self.coordinator.run_detection_cycle(
                    server=server,
                    service=service,
                    monitoring_snapshot={
                        "current_metrics": metrics,
                        "baseline_metrics": baseline,
                        "recent_log_lines": [],
                        "recent_deploys": [],
                    },
                )
            except AlibabaCloudNotConfiguredError:
                logger.warning(
                    "Alibaba Cloud credentials not configured — stopping monitoring loop for %s. "
                    "Set ALIBABA_CLOUD_ACCESS_KEY / ALIBABA_CLOUD_SECRET_KEY in .env to enable live monitoring.",
                    server,
                )
                return
            except NotImplementedError:
                logger.warning(
                    "fetch_instance_metrics for %s is not wired to a real CloudMonitor call yet "
                    "(see docs/architecture.md) — stopping monitoring loop for this server.",
                    server,
                )
                return
            except Exception:
                logger.exception("Unexpected error polling %s — will retry next cycle", server)

            await asyncio.sleep(settings.poll_interval_seconds)

    def _update_and_get_baseline(self, server: str, metrics: dict[str, float]) -> dict[str, float]:
        """Maintains a simple rolling mean/stddev per metric per server, in memory."""
        server_history = self._baselines.setdefault(server, {})
        baseline: dict[str, float] = {}

        for key, value in metrics.items():
            history = server_history.setdefault(key, deque(maxlen=BASELINE_WINDOW_SIZE))
            if history:
                mean = sum(history) / len(history)
                variance = sum((x - mean) ** 2 for x in history) / len(history)
                baseline[f"{key}_mean"] = round(mean, 2)
                baseline[f"{key}_std"] = round(variance ** 0.5, 2)
            history.append(value)

        return baseline


_monitor_loop: MonitorLoop | None = None


def get_monitor_loop(coordinator: Coordinator) -> MonitorLoop:
    global _monitor_loop
    if _monitor_loop is None:
        _monitor_loop = MonitorLoop(coordinator)
    return _monitor_loop
