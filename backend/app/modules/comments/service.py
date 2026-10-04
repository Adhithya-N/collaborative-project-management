"""Business logic for comments.

Authorization (who's allowed to edit/delete) lives in dependencies.py, not here - by the time
these functions run, the router's dependency has already confirmed the caller is allowed.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.activity.service import record_activity
from app.modules.comments.models import Comment
from app.modules.comments.schemas import CommentCreate, CommentUpdate
from app.modules.notifications.service import create_notification
from app.modules.tasks.models import Task
from app.modules.users.models import User
from app.realtime.event_bus import publish


def create_comment(db: Session, task_id: uuid.UUID, data: CommentCreate, current_user: User) -> Comment:
    """Adds a comment to a task and records it in the task's activity log, in one transaction."""
    comment = Comment(task_id=task_id, author_id=current_user.id, body=data.body)
    db.add(comment)
    db.flush()  # assigns comment.id, still part of the same transaction as the activity log entry

    record_activity(
        db,
        task_id=task_id,
        actor_id=current_user.id,
        action="commented",
        metadata={"comment_id": str(comment.id)},
    )

    task = db.get(Task, task_id)
    if task is not None and task.assignee_id is not None and task.assignee_id != current_user.id:
        create_notification(
            db,
            user_id=task.assignee_id,
            type_="new_comment",
            payload={"task_id": str(task_id), "comment_id": str(comment.id)},
        )

    db.commit()
    db.refresh(comment)

    if task is not None:
        publish(
            task.project_id,
            "comment.created",
            {"task_id": str(task_id), "comment_id": str(comment.id), "author_id": str(current_user.id)},
        )

    return comment


def list_comments(db: Session, task_id: uuid.UUID) -> list[Comment]:
    """Returns every comment on a task, oldest first."""
    return list(
        db.execute(select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)).scalars()
    )


def update_comment(db: Session, comment: Comment, data: CommentUpdate) -> Comment:
    """Edits a comment's text."""
    comment.body = data.body
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment: Comment) -> None:
    """Permanently removes a comment."""
    db.delete(comment)
    db.commit()
