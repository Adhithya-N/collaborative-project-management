"""HTTP routes for tasks."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.projects.dependencies import require_project_role
from app.modules.projects.models import ProjectRole
from app.modules.tasks.dependencies import require_task_project_role
from app.modules.tasks.models import Task, TaskStatus
from app.modules.tasks.schemas import TaskCreate, TaskRead, TaskUpdate
from app.modules.tasks.service import create_task, delete_task, list_tasks, update_task
from app.modules.users.models import User

# Nested under a project - creating/listing tasks (the task board) is scoped to one project.
project_tasks_router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])

# Task-scoped routes - task_id alone is enough, since the task already knows its project.
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@project_tasks_router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task_route(
    project_id: uuid.UUID,
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _membership: object = Depends(require_project_role(ProjectRole.CONTRIBUTOR)),
) -> TaskRead:
    task = create_task(db, project_id, data, current_user)
    return TaskRead.model_validate(task)


@project_tasks_router.get("", response_model=list[TaskRead])
def list_tasks_route(
    project_id: uuid.UUID,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _membership: object = Depends(require_project_role(ProjectRole.CONTRIBUTOR)),
) -> list[TaskRead]:
    tasks = list_tasks(db, project_id, status_filter)
    return [TaskRead.model_validate(t) for t in tasks]


@tasks_router.get("/{task_id}", response_model=TaskRead)
def get_task_route(
    task: Task = Depends(require_task_project_role(ProjectRole.CONTRIBUTOR)),
) -> TaskRead:
    return TaskRead.model_validate(task)


@tasks_router.patch("/{task_id}", response_model=TaskRead)
def update_task_route(
    data: TaskUpdate,
    db: Session = Depends(get_db),
    task: Task = Depends(require_task_project_role(ProjectRole.CONTRIBUTOR)),
) -> TaskRead:
    updated = update_task(db, task, data)
    return TaskRead.model_validate(updated)


@tasks_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_route(
    db: Session = Depends(get_db),
    task: Task = Depends(require_task_project_role(ProjectRole.LEAD)),
) -> None:
    delete_task(db, task)
