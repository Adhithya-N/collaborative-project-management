"""FastAPI dependencies enforcing comment-level access rules."""

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.comments.models import Comment
from app.modules.projects.models import ProjectMember, ProjectRole
from app.modules.tasks.models import Task
from app.modules.users.models import User


def get_comment(comment_id: uuid.UUID, db: Session = Depends(get_db)) -> Comment:
    """Loads a comment by id, or raises 404 if it doesn't exist."""
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment


def require_comment_author(
    comment: Comment = Depends(get_comment),
    current_user: User = Depends(get_current_user),
) -> Comment:
    """Only the original author may edit their own comment - no exceptions, not even a project lead."""
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own comments")
    return comment


def require_comment_author_or_lead(
    comment: Comment = Depends(get_comment),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Comment:
    """The author, or a project lead, may delete a comment (basic moderation power)."""
    if comment.author_id == current_user.id:
        return comment

    task = db.get(Task, comment.task_id)
    membership = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == task.project_id, ProjectMember.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if membership is None or membership.role != ProjectRole.LEAD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author or a project lead can delete this comment",
        )

    return comment
