"""Pydantic schemas for the comments module."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    """What the client sends to add a comment to a task."""

    body: str = Field(min_length=1, max_length=5000)


class CommentUpdate(BaseModel):
    """What the client sends to edit their own comment."""

    body: str = Field(min_length=1, max_length=5000)


class CommentRead(BaseModel):
    """Comment data sent back to the client."""

    id: uuid.UUID
    task_id: uuid.UUID
    author_id: uuid.UUID
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
