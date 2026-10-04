"""HTTP routes for comments on tasks."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.comments.dependencies import require_comment_author, require_comment_author_or_lead
from app.modules.comments.models import Comment
from app.modules.comments.schemas import CommentCreate, CommentRead, CommentUpdate
from app.modules.comments.service import create_comment, delete_comment, list_comments, update_comment
from app.modules.projects.models import ProjectRole
from app.modules.tasks.dependencies import require_task_project_role
from app.modules.tasks.models import Task
from app.modules.users.models import User

# Nested under a task - listing/creating comments is scoped to one task.
task_comments_router = APIRouter(prefix="/tasks/{task_id}/comments", tags=["comments"])

# Comment-scoped routes - comment_id alone is enough for editing/deleting a specific comment.
comments_router = APIRouter(prefix="/comments", tags=["comments"])


@task_comments_router.post("", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def create_comment_route(
    task_id: uuid.UUID,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _task: Task = Depends(require_task_project_role(ProjectRole.CONTRIBUTOR)),
) -> CommentRead:
    comment = create_comment(db, task_id, data, current_user)
    return CommentRead.model_validate(comment)


@task_comments_router.get("", response_model=list[CommentRead])
def list_comments_route(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    _task: Task = Depends(require_task_project_role(ProjectRole.CONTRIBUTOR)),
) -> list[CommentRead]:
    comments = list_comments(db, task_id)
    return [CommentRead.model_validate(c) for c in comments]


@comments_router.patch("/{comment_id}", response_model=CommentRead)
def update_comment_route(
    data: CommentUpdate,
    db: Session = Depends(get_db),
    comment: Comment = Depends(require_comment_author),
) -> CommentRead:
    updated = update_comment(db, comment, data)
    return CommentRead.model_validate(updated)


@comments_router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment_route(
    db: Session = Depends(get_db),
    comment: Comment = Depends(require_comment_author_or_lead),
) -> None:
    delete_comment(db, comment)
