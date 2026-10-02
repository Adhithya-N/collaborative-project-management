"""Pydantic schemas for the organizations module."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.organizations.models import OrgRole


class OrganizationCreate(BaseModel):
    """What the client sends to create a new organization."""

    name: str = Field(min_length=1, max_length=255)
    # Lowercase letters, numbers, hyphens only - keeps it safe to use directly in future URLs.
    slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")


class OrganizationRead(BaseModel):
    """Organization data sent back to the client."""

    id: uuid.UUID
    name: str
    slug: str
    created_by: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberInvite(BaseModel):
    """What the client sends to add an already-registered user to an organization."""

    email: EmailStr
    role: OrgRole = OrgRole.MEMBER


class MemberRoleUpdate(BaseModel):
    """What the client sends to change an existing member's role."""

    role: OrgRole


class MemberRead(BaseModel):
    """Membership data sent back to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    role: OrgRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
