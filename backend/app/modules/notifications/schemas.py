"""Pydantic schemas for the notifications module."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    """Notification data sent back to the client."""

    id: uuid.UUID
    type: str
    payload: dict
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
