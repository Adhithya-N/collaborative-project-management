"""FastAPI dependencies that enforce 'are you a member?' / 'do you have enough role?' checks."""

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.organizations.models import OrganizationMember, OrgRole
from app.modules.users.models import User

# Numeric ranking so roles can be compared ("is this role at least as powerful as that one?").
_ROLE_RANK = {OrgRole.MEMBER: 0, OrgRole.ADMIN: 1, OrgRole.OWNER: 2}


def get_org_membership(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMember:
    """Confirms the current user belongs to the org named in the URL, or rejects the request with 403."""
    membership = db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id, OrganizationMember.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")

    return membership


def require_role(minimum: OrgRole):
    """Dependency factory - e.g. require_role(OrgRole.ADMIN) only lets admins and owners through."""

    def checker(membership: OrganizationMember = Depends(get_org_membership)) -> OrganizationMember:
        if _ROLE_RANK[membership.role] < _ROLE_RANK[minimum]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this action")
        return membership

    return checker
