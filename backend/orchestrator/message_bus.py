"""
In-process message bus connecting agents to each other and to WebSocket
subscribers (the frontend).

This is intentionally simple — an asyncio pub/sub, not a distributed broker —
because all agents run in the same process for this system. If Aegis needs to
scale agents across processes/machines later, this is the seam to swap for
Redis pub/sub or a proper message queue without touching agent code.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable

logger = logging.getLogger("aegis.message_bus")

Handler = Callable[[dict[str, Any]], Awaitable[None]]


class MessageBus:
    """Topic-based async pub/sub used to fan incident events out to subscribers."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._subscribers[topic].append(handler)
        logger.debug("Subscribed handler to topic '%s'", topic)

    def unsubscribe(self, topic: str, handler: Handler) -> None:
        if handler in self._subscribers.get(topic, []):
            self._subscribers[topic].remove(handler)

    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        handlers = self._subscribers.get(topic, [])
        if not handlers:
            return
        # Run handlers concurrently; one slow/broken subscriber (e.g. a dropped
        # WebSocket) should never block the orchestration pipeline.
        results = await asyncio.gather(*(h(message) for h in handlers), return_exceptions=True)
        for handler, result in zip(handlers, results):
            if isinstance(result, Exception):
                logger.error("Handler %s on topic '%s' raised: %s", handler, topic, result)


_bus: MessageBus | None = None


def get_message_bus() -> MessageBus:
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus


# Well-known topics, kept as constants so typos don't silently create dead topics.
TOPIC_INCIDENT_CREATED = "incident.created"
TOPIC_INCIDENT_UPDATED = "incident.updated"
TOPIC_AGENT_STATUS_CHANGED = "agent.status_changed"
TOPIC_TIMELINE_EVENT = "incident.timeline_event"
TOPIC_APPROVAL_REQUIRED = "incident.approval_required"
TOPIC_REPORT_GENERATED = "incident.report_generated"
