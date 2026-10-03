"""Pydantic schemas for the projects module."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.projects.models import ProjectRole


class ProjectCreate(BaseModel):
    """What the client sends to create a new project within an organization."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectRead(BaseModel):
    """Project data sent back to the client."""

    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: str | None
    created_by: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberAdd(BaseModel):
    """What the client sends to add an org member to a project.

    Uses user_id (not email) since the target user must already be a known member of the
    project's organization - the frontend would list org members to pick from.
    """

    user_id: uuid.UUID
    role: ProjectRole = ProjectRole.CONTRIBUTOR


class ProjectMemberRoleUpdate(BaseModel):
    """What the client sends to change an existing project member's role."""

    role: ProjectRole


class ProjectMemberRead(BaseModel):
    """Project membership data sent back to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    role: ProjectRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
