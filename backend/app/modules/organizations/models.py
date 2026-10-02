"""Database models for organizations - the top-level container everything else belongs to."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OrgRole(str, enum.Enum):
    """Fixed set of roles a user can hold within an organization."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Organization(Base):
    """A workspace that owns projects and has its own set of members."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Used in URLs later (e.g. /orgs/acme-corp) - must be unique and URL-safe.
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    members: Mapped[list["OrganizationMember"]] = relationship(back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base):
    """Links a User to an Organization with a specific role - one row per membership."""

    __tablename__ = "organization_members"
    __table_args__ = (
        # A user can only belong to a given org once.
        UniqueConstraint("org_id", "user_id", name="uq_org_member"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role: Mapped[OrgRole] = mapped_column(
        PgEnum(OrgRole, name="org_role", values_callable=lambda e: [member.value for member in e]),
        nullable=False,
        default=OrgRole.MEMBER,
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="members")
