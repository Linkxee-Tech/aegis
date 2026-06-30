"""
In-process message bus connecting agents to each other and to WebSocket
subscribers (the frontend).

Now upgraded to use Model Context Protocol (MCP) message schemas (JSON-RPC 2.0)
and backed by Redis pub/sub.
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from typing import Any, Awaitable, Callable

import redis.asyncio as redis

from backend.config.settings import get_settings

logger = logging.getLogger("aegis.message_bus")
settings = get_settings()

# A handler takes an MCP JSON-RPC message dict
Handler = Callable[[dict[str, Any]], Awaitable[None]]

def create_mcp_message(method: str, params: dict[str, Any]) -> dict[str, Any]:
    """Wraps a payload in a Model Context Protocol (MCP) JSON-RPC 2.0 envelope."""
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": str(uuid.uuid4())
    }

class MessageBus:
    """Topic-based async pub/sub used to fan incident events out to subscribers via MCP over Redis."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        self._listen_task: asyncio.Task | None = None
        self._subscribed_topics: set[str] = set()

    async def _listen_loop(self):
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    topic = message["channel"]
                    try:
                        mcp_envelope = json.loads(message["data"])
                    except json.JSONDecodeError:
                        continue
                        
                    handlers = self._subscribers.get(topic, [])
                    if handlers:
                        results = await asyncio.gather(*(h(mcp_envelope) for h in handlers), return_exceptions=True)
                        for handler, result in zip(handlers, results):
                            if isinstance(result, Exception):
                                logger.error("Handler %s on topic '%s' raised: %s", handler, topic, result)
        except asyncio.CancelledError:
            logger.info("Redis pub/sub listen loop cancelled")
        except Exception as e:
            logger.error("Redis pub/sub listen loop error: %s", e)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._subscribers[topic].append(handler)
        if topic not in self._subscribed_topics:
            self._subscribed_topics.add(topic)
            asyncio.create_task(self._pubsub.subscribe(topic))
            if self._listen_task is None or self._listen_task.done():
                self._listen_task = asyncio.create_task(self._listen_loop())
        logger.debug("Subscribed handler to topic '%s'", topic)

    def unsubscribe(self, topic: str, handler: Handler) -> None:
        if handler in self._subscribers.get(topic, []):
            self._subscribers[topic].remove(handler)
        if not self._subscribers.get(topic):
            self._subscribed_topics.discard(topic)
            asyncio.create_task(self._pubsub.unsubscribe(topic))

    async def publish(self, topic: str, message: dict[str, Any]) -> None:
        mcp_envelope = create_mcp_message(method=topic, params=message)
        await self._redis.publish(topic, json.dumps(mcp_envelope))

_bus: MessageBus | None = None

def get_message_bus() -> MessageBus:
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus


# Well-known topics (now mapped as MCP methods)
TOPIC_INCIDENT_CREATED = "incident.created"
TOPIC_INCIDENT_UPDATED = "incident.updated"
TOPIC_AGENT_STATUS_CHANGED = "agent.status_changed"
TOPIC_TIMELINE_EVENT = "incident.timeline_event"
TOPIC_APPROVAL_REQUIRED = "incident.approval_required"
TOPIC_REPORT_GENERATED = "incident.report_generated"
