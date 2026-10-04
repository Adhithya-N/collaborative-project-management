"""HTTP routes for viewing a task's activity log."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.activity.schemas import ActivityRead
from app.modules.activity.service import list_activity
from app.modules.projects.models import ProjectRole
from app.modules.tasks.dependencies import require_task_project_role
from app.modules.tasks.models import Task

router = APIRouter(prefix="/tasks/{task_id}/activity", tags=["activity"])


@router.get("", response_model=list[ActivityRead])
def list_activity_route(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    _task: Task = Depends(require_task_project_role(ProjectRole.CONTRIBUTOR)),
) -> list[ActivityRead]:
    entries = list_activity(db, task_id)
    return [ActivityRead.model_validate(e) for e in entries]
