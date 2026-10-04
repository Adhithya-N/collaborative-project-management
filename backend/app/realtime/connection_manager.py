"""In-process WebSocket connection registry, keyed by project.

This is intentionally the ONLY place in the codebase that knows about live WebSocket
connections. If the app ever needs to run on multiple server instances, only `event_bus.py`
would need to change (e.g. to use Redis pub/sub instead) - no other code would be touched.
"""

import asyncio
import uuid

from fastapi import WebSocket


class ConnectionManager:
    """Tracks which WebSocket connections are currently watching which project."""

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = {}
        # Captured once at app startup (see main.py's lifespan) - lets sync service-layer code
        # schedule an async broadcast even though it has no event loop of its own.
        self.loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, project_id: uuid.UUID, websocket: WebSocket) -> None:
        """Accepts a new WebSocket connection and registers it under a project."""
        await websocket.accept()
        self._connections.setdefault(project_id, set()).add(websocket)

    def disconnect(self, project_id: uuid.UUID, websocket: WebSocket) -> None:
        """Removes a connection (called when a client disconnects or a send fails)."""
        connections = self._connections.get(project_id)
        if connections is not None:
            connections.discard(websocket)
            if not connections:
                del self._connections[project_id]

    async def broadcast(self, project_id: uuid.UUID, message: dict) -> None:
        """Sends a JSON message to every client currently watching this project."""
        for websocket in list(self._connections.get(project_id, set())):
            try:
                await websocket.send_json(message)
            except Exception:
                # Connection is likely already broken/closed - clean it up instead of crashing.
                self.disconnect(project_id, websocket)

    def broadcast_from_sync(self, project_id: uuid.UUID, message: dict) -> None:
        """Entry point for regular (non-async) service-layer code to trigger a broadcast.

        Our routes and services are plain `def` functions, run by FastAPI in a worker thread -
        they have no running event loop. `run_coroutine_threadsafe` hands the broadcast off to
        the main event loop, where the actual WebSocket connections live.
        """
        if self.loop is None:
            return  # no event loop registered yet (e.g. during startup/tests) - skip silently
        asyncio.run_coroutine_threadsafe(self.broadcast(project_id, message), self.loop)


# Single shared instance - imported wherever a connection needs to register or a broadcast needs to happen.
manager = ConnectionManager()
