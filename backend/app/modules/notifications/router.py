"""HTTP routes for notifications - always scoped to 'my own' notifications."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.notifications.dependencies import get_own_notification
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationRead
from app.modules.notifications.service import list_notifications, mark_all_as_read, mark_as_read
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications_route(
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotificationRead]:
    notifications = list_notifications(db, current_user.id, unread_only)
    return [NotificationRead.model_validate(n) for n in notifications]


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read_route(
    db: Session = Depends(get_db),
    notification: Notification = Depends(get_own_notification),
) -> NotificationRead:
    updated = mark_as_read(db, notification)
    return NotificationRead.model_validate(updated)


@router.patch("/read-all", status_code=204)
def mark_all_notifications_read_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    mark_all_as_read(db, current_user.id)
