"""Thin, swappable abstraction over real-time broadcasting.

Every module that wants to push a real-time update calls `publish()` - it has no idea whether
the actual mechanism is an in-process ConnectionManager (now, single server instance) or Redis
pub/sub across multiple instances (later, if the app ever needs to scale horizontally). Only
this function's internals would change to support that - callers never would.
"""

import uuid

from app.realtime.connection_manager import manager


def publish(project_id: uuid.UUID, event_type: str, data: dict) -> None:
    """Broadcasts an event to every client currently connected to this project's WebSocket room."""
    manager.broadcast_from_sync(project_id, {"type": event_type, "data": data})
