"""Business logic for the activity log.

This module is deliberately 'dumb' - it knows nothing about tasks, comments, or any other
domain concept. Other modules (tasks, comments) call `record_activity()` after their own action
succeeds, passing in whatever details matter. This keeps the dependency one-directional:
tasks/comments depend on activity, but activity never depends on them.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.activity.models import ActivityLog


def record_activity(
    db: Session, task_id: uuid.UUID, actor_id: uuid.UUID, action: str, metadata: dict | None = None
) -> ActivityLog:
    """Appends one event to a task's activity log.

    Does NOT commit - the caller's own transaction (e.g. a task update) owns the commit, so the
    activity entry either saves together with the real change, or rolls back together with it.
    """
    entry = ActivityLog(task_id=task_id, actor_id=actor_id, action=action, activity_metadata=metadata or {})
    db.add(entry)
    db.flush()  # assigns entry.id without ending the caller's transaction
    return entry


def list_activity(db: Session, task_id: uuid.UUID) -> list[ActivityLog]:
    """Returns the full activity history for a task, oldest first."""
    return list(
        db.execute(
            select(ActivityLog).where(ActivityLog.task_id == task_id).order_by(ActivityLog.created_at)
        ).scalars()
    )
