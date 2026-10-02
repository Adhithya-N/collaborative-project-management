"""Business logic for organizations and their membership."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.organizations.models import Organization, OrganizationMember, OrgRole
from app.modules.organizations.schemas import MemberInvite, OrganizationCreate
from app.modules.users.models import User


def create_organization(db: Session, data: OrganizationCreate, current_user: User) -> Organization:
    """Creates an organization and makes the creator its first member, with the owner role."""
    existing = db.execute(select(Organization).where(Organization.slug == data.slug)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already in use")

    org = Organization(name=data.name, slug=data.slug, created_by=current_user.id)
    db.add(org)
    db.flush()  # assigns org.id without ending the transaction, so we can reference it below

    db.add(OrganizationMember(org_id=org.id, user_id=current_user.id, role=OrgRole.OWNER))
    db.commit()
    db.refresh(org)
    return org


def list_my_organizations(db: Session, current_user: User) -> list[Organization]:
    """Returns every organization the current user belongs to."""
    return list(
        db.execute(
            select(Organization)
            .join(OrganizationMember, OrganizationMember.org_id == Organization.id)
            .where(OrganizationMember.user_id == current_user.id)
        ).scalars()
    )


def list_members(db: Session, org_id: uuid.UUID) -> list[OrganizationMember]:
    """Returns every membership row for an organization."""
    return list(db.execute(select(OrganizationMember).where(OrganizationMember.org_id == org_id)).scalars())


def add_member(db: Session, org_id: uuid.UUID, data: MemberInvite) -> OrganizationMember:
    """Adds an already-registered user to an organization. (Inviting non-users by email comes later.)"""
    user = db.execute(select(User).where(User.email == data.email)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No registered user with that email")

    existing = db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id, OrganizationMember.user_id == user.id
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member")

    membership = OrganizationMember(org_id=org_id, user_id=user.id, role=data.role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def remove_member(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Removes a member from an organization."""
    membership = db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id, OrganizationMember.user_id == user_id
        )
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

    db.delete(membership)
    db.commit()
