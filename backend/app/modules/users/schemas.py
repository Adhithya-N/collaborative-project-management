"""Pydantic schemas for the users module - define what data goes in/out of the API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    """Safe representation of a User to send back in API responses - never includes the password."""

    id: uuid.UUID
    email: str
    full_name: str
    created_at: datetime

    # Lets Pydantic read values directly from the SQLAlchemy User object's attributes.
    model_config = ConfigDict(from_attributes=True)
