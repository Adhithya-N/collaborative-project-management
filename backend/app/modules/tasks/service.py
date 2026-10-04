"""Business logic for tasks."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.activity.service import record_activity
from app.modules.notifications.service import create_notification
from app.modules.projects.models import ProjectMember
from app.modules.tasks.models import Task, TaskStatus
from app.modules.tasks.schemas import TaskCreate, TaskUpdate
from app.modules.users.models import User
from app.realtime.event_bus import publish


def _validate_assignee(db: Session, project_id: uuid.UUID, assignee_id: uuid.UUID | None) -> None:
    """An assignee must already be a member of the task's project (same rule as project membership itself)."""
    if assignee_id is None:
        return
    membership = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == assignee_id
        )
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Assignee must be a member of this project"
        )


def create_task(db: Session, project_id: uuid.UUID, data: TaskCreate, current_user: User) -> Task:
    """Creates a task within a project and records the creation in its activity log."""
    _validate_assignee(db, project_id, data.assignee_id)

    task = Task(
        project_id=project_id,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        assignee_id=data.assignee_id,
        created_by=current_user.id,
        due_date=data.due_date,
    )
    db.add(task)
    db.flush()  # assigns task.id, still part of the same transaction as the activity log entry

    record_activity(db, task_id=task.id, actor_id=current_user.id, action="created", metadata={"title": task.title})

    if task.assignee_id is not None and task.assignee_id != current_user.id:
        create_notification(
            db,
            user_id=task.assignee_id,
            type_="task_assigned",
            payload={"task_id": str(task.id), "task_title": task.title},
        )

    db.commit()
    db.refresh(task)

    # Broadcast AFTER commit - never push state to clients that could still roll back.
    publish(
        task.project_id,
        "task.created",
        {"task_id": str(task.id), "title": task.title, "status": task.status.value},
    )
    return task


def list_tasks(db: Session, project_id: uuid.UUID, status_filter: TaskStatus | None = None) -> list[Task]:
    """Returns tasks in a project, optionally filtered by status - the task board's main query."""
    query = select(Task).where(Task.project_id == project_id)
    if status_filter is not None:
        query = query.where(Task.status == status_filter)
    return list(db.execute(query).scalars())


def update_task(db: Session, task: Task, data: TaskUpdate, current_user: User) -> Task:
    """Applies only the fields the client actually sent, logging status/assignment changes as activity."""
    updates = data.model_dump(exclude_unset=True)

    if "assignee_id" in updates:
        _validate_assignee(db, task.project_id, updates["assignee_id"])

    old_status = task.status
    old_assignee_id = task.assignee_id

    for field, value in updates.items():
        setattr(task, field, value)

    if "status" in updates and task.status != old_status:
        record_activity(
            db,
            task_id=task.id,
            actor_id=current_user.id,
            action="status_changed",
            metadata={"from": old_status.value, "to": task.status.value},
        )

    if "assignee_id" in updates and task.assignee_id != old_assignee_id:
        record_activity(
            db,
            task_id=task.id,
            actor_id=current_user.id,
            action="assigned",
            metadata={"assignee_id": str(task.assignee_id) if task.assignee_id else None},
        )

        if task.assignee_id is not None and task.assignee_id != current_user.id:
            create_notification(
                db,
                user_id=task.assignee_id,
                type_="task_assigned",
                payload={"task_id": str(task.id), "task_title": task.title},
            )

    db.commit()
    db.refresh(task)

    publish(
        task.project_id,
        "task.updated",
        {"task_id": str(task.id), "status": task.status.value, "assignee_id": str(task.assignee_id) if task.assignee_id else None},
    )
    return task


def delete_task(db: Session, task: Task) -> None:
    """Permanently removes a task."""
    db.delete(task)
    db.commit()
