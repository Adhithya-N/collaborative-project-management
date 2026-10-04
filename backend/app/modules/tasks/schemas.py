"""Pydantic schemas for the tasks module."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.tasks.models import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    """What the client sends to create a new task."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: uuid.UUID | None = None
    due_date: date | None = None


class TaskUpdate(BaseModel):
    """What the client sends to edit a task - every field is optional (partial update)."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: uuid.UUID | None = None
    due_date: date | None = None


class TaskRead(BaseModel):
    """Task data sent back to the client."""

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    assignee_id: uuid.UUID | None
    created_by: uuid.UUID
    due_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
