"""FastAPI dependencies enforcing project-level access rules."""

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.organizations.models import OrganizationMember
from app.modules.projects.models import Project, ProjectMember, ProjectRole
from app.modules.users.models import User

# Numeric ranking so roles can be compared.
_ROLE_RANK = {ProjectRole.CONTRIBUTOR: 0, ProjectRole.LEAD: 1}


def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> Project:
    """Loads a project by id, or raises 404 if it doesn't exist."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def require_org_membership_for_project(
    project: Project = Depends(get_project),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    """Confirms the current user belongs to the project's parent organization (view-level access)."""
    membership = db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == project.org_id, OrganizationMember.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this project's organization"
        )

    return project


def get_project_membership(
    project: Project = Depends(get_project),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectMember:
    """Confirms the current user is specifically assigned to this project (not just the org)."""
    membership = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id, ProjectMember.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this project")

    return membership


def require_project_role(minimum: ProjectRole):
    """Dependency factory - e.g. require_project_role(ProjectRole.LEAD) only lets leads through."""

    def checker(membership: ProjectMember = Depends(get_project_membership)) -> ProjectMember:
        if _ROLE_RANK[membership.role] < _ROLE_RANK[minimum]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient project role")
        return membership

    return checker
