"""Business logic for notifications.

Like activity.service.record_activity(), create_notification() is a one-directional utility -
other modules (tasks, comments) call into it, it never calls back into them.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification


def create_notification(db: Session, user_id: uuid.UUID, type_: str, payload: dict | None = None) -> Notification:
    """Creates a notification for a user.

    Does NOT commit - the caller's own transaction owns that, so the notification is saved (or
    rolled back) together with whatever real action triggered it.
    """
    notification = Notification(user_id=user_id, type=type_, payload=payload or {})
    db.add(notification)
    db.flush()  # assigns notification.id without ending the caller's transaction
    return notification


def list_notifications(db: Session, user_id: uuid.UUID, unread_only: bool = False) -> list[Notification]:
    """Returns a user's notifications, newest first."""
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    query = query.order_by(Notification.created_at.desc())
    return list(db.execute(query).scalars())


def mark_as_read(db: Session, notification: Notification) -> Notification:
    """Flips a single notification to read."""
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_as_read(db: Session, user_id: uuid.UUID) -> None:
    """Flips every unread notification for a user to read in one go."""
    notifications = list_notifications(db, user_id, unread_only=True)
    for notification in notifications:
        notification.is_read = True
    db.commit()
