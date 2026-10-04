"""FastAPI dependencies enforcing notification-level access rules."""

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.notifications.models import Notification
from app.modules.users.models import User


def get_own_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notification:
    """Loads a notification, but only if it belongs to the current user - otherwise 404.

    Returns 404 (not 403) for someone else's notification - this avoids leaking whether a
    given notification ID even exists to users who shouldn't see it.
    """
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notification
