"""Business logic for projects and their membership."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.organizations.models import OrganizationMember
from app.modules.projects.models import Project, ProjectMember, ProjectRole
from app.modules.projects.schemas import ProjectCreate, ProjectMemberAdd, ProjectMemberRoleUpdate
from app.modules.users.models import User


def create_project(db: Session, org_id: uuid.UUID, data: ProjectCreate, current_user: User) -> Project:
    """Creates a project within an organization and makes the creator its first member, as lead."""
    project = Project(org_id=org_id, name=data.name, description=data.description, created_by=current_user.id)
    db.add(project)
    db.flush()  # assigns project.id without ending the transaction, so we can reference it below

    db.add(ProjectMember(project_id=project.id, user_id=current_user.id, role=ProjectRole.LEAD))
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, org_id: uuid.UUID) -> list[Project]:
    """Returns every project belonging to an organization."""
    return list(db.execute(select(Project).where(Project.org_id == org_id)).scalars())


def list_project_members(db: Session, project_id: uuid.UUID) -> list[ProjectMember]:
    """Returns every membership row for a project."""
    return list(db.execute(select(ProjectMember).where(ProjectMember.project_id == project_id)).scalars())


def add_project_member(db: Session, project: Project, data: ProjectMemberAdd) -> ProjectMember:
    """Adds an org member to a project. The user MUST already belong to the project's organization."""
    org_membership = db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == project.org_id, OrganizationMember.user_id == data.user_id
        )
    ).scalar_one_or_none()
    if org_membership is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be a member of the organization before being added to a project",
        )

    existing = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id, ProjectMember.user_id == data.user_id
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a project member")

    membership = ProjectMember(project_id=project.id, user_id=data.user_id, role=data.role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def remove_project_member(db: Session, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Removes a member from a project."""
    membership = db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project membership not found")

    db.delete(membership)
    db.commit()


def update_project_member_role(
    db: Session, project_id: uuid.UUID, user_id: uuid.UUID, data: ProjectMemberRoleUpdate
) -> ProjectMember:
    """Promotes or demotes an existing project member (contributor <-> lead)."""
    membership = db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project membership not found")

    membership.role = data.role
    db.commit()
    db.refresh(membership)
    return membership
