"""WebSocket endpoint for real-time project updates."""

import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import ALGORITHM
from app.modules.projects.models import ProjectMember
from app.realtime.connection_manager import manager

router = APIRouter()


def _authenticate_websocket(token: str, project_id: uuid.UUID) -> bool:
    """Verifies the JWT and confirms the user belongs to this project - same access level as viewing tasks.

    WebSocket connections can't use the normal `Depends(get_current_user)` HTTP dependency, since
    there's no Authorization header during the handshake - the token is passed as a query param
    instead, and verified manually here before the connection is accepted.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        return False
    if user_id is None:
        return False

    db = SessionLocal()
    try:
        membership = db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
            )
        ).scalar_one_or_none()
        return membership is not None
    finally:
        db.close()


@router.websocket("/ws/projects/{project_id}")
async def project_websocket(websocket: WebSocket, project_id: uuid.UUID, token: str) -> None:
    """One connection per client watching a project's live updates."""
    if not _authenticate_websocket(token, project_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(project_id, websocket)
    try:
        while True:
            # Clients aren't expected to send anything - this just blocks until disconnect,
            # which is how we detect the connection closing.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(project_id, websocket)
