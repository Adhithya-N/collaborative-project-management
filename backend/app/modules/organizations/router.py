"""HTTP routes for organizations and their membership."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.organizations.dependencies import require_role
from app.modules.organizations.models import OrgRole
from app.modules.organizations.schemas import MemberInvite, MemberRead, MemberRoleUpdate, OrganizationCreate, OrganizationRead
from app.modules.organizations.service import (
    add_member,
    create_organization,
    list_members,
    list_my_organizations,
    remove_member,
    update_member_role,
)
from app.modules.users.models import User

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_org(
    data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationRead:
    org = create_organization(db, data, current_user)
    return OrganizationRead.model_validate(org)


@router.get("", response_model=list[OrganizationRead])
def list_orgs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrganizationRead]:
    orgs = list_my_organizations(db, current_user)
    return [OrganizationRead.model_validate(org) for org in orgs]


@router.get("/{org_id}/members", response_model=list[MemberRead])
def get_members(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership: object = Depends(require_role(OrgRole.MEMBER)),
) -> list[MemberRead]:
    members = list_members(db, org_id)
    return [MemberRead.model_validate(m) for m in members]


@router.post("/{org_id}/members", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def invite_member(
    org_id: uuid.UUID,
    data: MemberInvite,
    db: Session = Depends(get_db),
    _membership: object = Depends(require_role(OrgRole.ADMIN)),
) -> MemberRead:
    membership = add_member(db, org_id, data)
    return MemberRead.model_validate(membership)


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership: object = Depends(require_role(OrgRole.ADMIN)),
) -> None:
    remove_member(db, org_id, user_id)


@router.patch("/{org_id}/members/{user_id}", response_model=MemberRead)
def change_member_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    data: MemberRoleUpdate,
    db: Session = Depends(get_db),
    _membership: object = Depends(require_role(OrgRole.ADMIN)),
) -> MemberRead:
    membership = update_member_role(db, org_id, user_id, data)
    return MemberRead.model_validate(membership)
