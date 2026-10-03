"""HTTP routes for projects and their membership."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.organizations.dependencies import get_org_membership
from app.modules.projects.dependencies import get_project, require_org_membership_for_project, require_project_role
from app.modules.projects.models import Project, ProjectRole
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectMemberRead,
    ProjectMemberRoleUpdate,
    ProjectRead,
)
from app.modules.projects.service import (
    add_project_member,
    create_project,
    list_project_members,
    list_projects,
    remove_project_member,
    update_project_member_role,
)
from app.modules.users.models import User

# Nested under an organization - creating/listing projects is scoped to a specific org.
org_projects_router = APIRouter(prefix="/organizations/{org_id}/projects", tags=["projects"])

# Project-scoped routes - project_id alone is enough, since the project already knows its org.
projects_router = APIRouter(prefix="/projects", tags=["projects"])


@org_projects_router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project_route(
    org_id: uuid.UUID,
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _membership: object = Depends(get_org_membership),
) -> ProjectRead:
    project = create_project(db, org_id, data, current_user)
    return ProjectRead.model_validate(project)


@org_projects_router.get("", response_model=list[ProjectRead])
def list_projects_route(
    org_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership: object = Depends(get_org_membership),
) -> list[ProjectRead]:
    projects = list_projects(db, org_id)
    return [ProjectRead.model_validate(p) for p in projects]


@projects_router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
def list_members_route(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    _project: Project = Depends(require_org_membership_for_project),
) -> list[ProjectMemberRead]:
    members = list_project_members(db, project_id)
    return [ProjectMemberRead.model_validate(m) for m in members]


@projects_router.post("/{project_id}/members", response_model=ProjectMemberRead, status_code=status.HTTP_201_CREATED)
def add_member_route(
    project_id: uuid.UUID,
    data: ProjectMemberAdd,
    db: Session = Depends(get_db),
    project: Project = Depends(get_project),
    _membership: object = Depends(require_project_role(ProjectRole.LEAD)),
) -> ProjectMemberRead:
    membership = add_project_member(db, project, data)
    return ProjectMemberRead.model_validate(membership)


@projects_router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberRead)
def update_member_role_route(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ProjectMemberRoleUpdate,
    db: Session = Depends(get_db),
    _membership: object = Depends(require_project_role(ProjectRole.LEAD)),
) -> ProjectMemberRead:
    membership = update_project_member_role(db, project_id, user_id, data)
    return ProjectMemberRead.model_validate(membership)


@projects_router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member_route(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership: object = Depends(require_project_role(ProjectRole.LEAD)),
) -> None:
    remove_project_member(db, project_id, user_id)
