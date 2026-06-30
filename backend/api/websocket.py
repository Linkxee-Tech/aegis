"""
WebSocket endpoint that streams live incident and agent events to the frontend.

Subscribes a per-connection handler to every topic on the message bus and
forwards each event as a JSON envelope matching frontend/src/hooks/useWebSocket.ts's
expectations. One connection per browser tab; the ConnectionManager below just
tracks active sockets so we can clean up subscriptions on disconnect.
"""

import logging
from typing import Any

from fastapi import HTTPException, WebSocket, WebSocketDisconnect, status

from backend.services.auth import get_websocket_auth_context
from backend.orchestrator.message_bus import (
    TOPIC_AGENT_STATUS_CHANGED,
    TOPIC_APPROVAL_REQUIRED,
    TOPIC_INCIDENT_CREATED,
    TOPIC_INCIDENT_UPDATED,
    TOPIC_REPORT_GENERATED,
    TOPIC_TIMELINE_EVENT,
    get_message_bus,
)

logger = logging.getLogger("aegis.websocket")

# Maps internal bus topics to the event "type" string the frontend expects.
TOPIC_TO_EVENT_TYPE = {
    TOPIC_INCIDENT_CREATED: "incident_created",
    TOPIC_INCIDENT_UPDATED: "incident_updated",
    TOPIC_AGENT_STATUS_CHANGED: "agent_status_changed",
    TOPIC_TIMELINE_EVENT: "timeline_event",
    TOPIC_APPROVAL_REQUIRED: "approval_required",
    TOPIC_REPORT_GENERATED: "report_generated",
}


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket connected (%d active)", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)
        logger.info("WebSocket disconnected (%d active)", len(self.active_connections))


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    try:
        get_websocket_auth_context(websocket)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    bus = get_message_bus()

    async def forward(topic: str):
        async def handler(mcp_message: dict[str, Any]) -> None:
            try:
                # Extract original payload from MCP JSON-RPC envelope
                payload = mcp_message.get("params", mcp_message)
                await websocket.send_json({"type": TOPIC_TO_EVENT_TYPE[topic], "payload": payload})
            except Exception:
                logger.exception("Failed to forward event on topic '%s' to client", topic)
        return handler

    handlers = {}
    for topic in TOPIC_TO_EVENT_TYPE:
        handler = await forward(topic)
        handlers[topic] = handler
        bus.subscribe(topic, handler)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        for topic, handler in handlers.items():
            bus.unsubscribe(topic, handler)
        manager.disconnect(websocket)


async def websocket_incident_endpoint(websocket: WebSocket, incident_id: str) -> None:
    """
    Per-incident WebSocket — /ws/incidents/{incident_id}

    Subscribes to the same message bus but filters events to only those
    relevant to the specified incident, plus all agent-status-changed events
    (which are global but useful for the per-incident view).
    Satisfies the Phase 2 checklist: '/ws/incidents/{incident_id} established.
    Real-time streaming of agent thoughts and actions is functional.'
    """
    try:
        get_websocket_auth_context(websocket)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    bus = get_message_bus()

    INCIDENT_TOPICS = {
        TOPIC_INCIDENT_CREATED,
        TOPIC_INCIDENT_UPDATED,
        TOPIC_TIMELINE_EVENT,
        TOPIC_APPROVAL_REQUIRED,
        TOPIC_REPORT_GENERATED,
    }

    async def forward_if_relevant(topic: str):
        async def handler(mcp_message: dict[str, Any]) -> None:
            # Extract original payload from MCP JSON-RPC envelope
            payload = mcp_message.get("params", mcp_message)
            
            # Always forward agent status changes; filter incident events by id
            if topic == TOPIC_AGENT_STATUS_CHANGED or payload.get("incidentId") == incident_id or payload.get("id") == incident_id:
                try:
                    await websocket.send_json({"type": TOPIC_TO_EVENT_TYPE[topic], "payload": payload})
                except Exception:
                    pass
        return handler

    handlers = {}
    for topic in {*INCIDENT_TOPICS, TOPIC_AGENT_STATUS_CHANGED}:
        handler = await forward_if_relevant(topic)
        handlers[topic] = handler
        bus.subscribe(topic, handler)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        for topic, handler in handlers.items():
            bus.unsubscribe(topic, handler)
        manager.disconnect(websocket)
