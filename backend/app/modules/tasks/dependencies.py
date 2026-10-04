"""FastAPI dependencies enforcing task-level access rules."""

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.projects.models import ProjectMember, ProjectRole
from app.modules.tasks.models import Task
from app.modules.users.models import User

# Numeric ranking so roles can be compared.
_ROLE_RANK = {ProjectRole.CONTRIBUTOR: 0, ProjectRole.LEAD: 1}


def get_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> Task:
    """Loads a task by id, or raises 404 if it doesn't exist."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def require_task_project_role(minimum: ProjectRole):
    """Dependency factory - confirms the user has at least `minimum` role in the task's project.

    Tasks don't have their own role/membership - access is always derived from the parent
    project's membership, since a task is just a piece of a project.
    """

    def checker(
        task: Task = Depends(get_task),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Task:
        membership = db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == task.project_id, ProjectMember.user_id == current_user.id
            )
        ).scalar_one_or_none()

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this task's project"
            )
        if _ROLE_RANK[membership.role] < _ROLE_RANK[minimum]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient project role")

        return task

    return checker
