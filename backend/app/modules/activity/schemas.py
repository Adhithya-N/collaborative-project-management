"""Pydantic schemas for the activity module."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityRead(BaseModel):
    """One activity log entry sent back to the client."""

    id: uuid.UUID
    task_id: uuid.UUID
    actor_id: uuid.UUID
    action: str
    activity_metadata: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
