"""Tests for project membership and task-level role-based access control."""

from fastapi.testclient import TestClient

from tests.conftest import register_and_login


def _create_org_and_project(client: TestClient, owner_headers: dict[str, str]) -> tuple[str, str]:
    """Helper: creates an org + a project inside it, returns (org_id, project_id)."""
    org_id = client.post(
        "/organizations", json={"name": "Test Org", "slug": "test-org"}, headers=owner_headers
    ).json()["id"]
    project_id = client.post(
        f"/organizations/{org_id}/projects",
        json={"name": "Test Project", "description": "A project for testing"},
        headers=owner_headers,
    ).json()["id"]
    return org_id, project_id


def test_creating_a_project_makes_creator_the_lead(client: TestClient) -> None:
    owner_headers = register_and_login(client, "lead_owner@example.com")
    _org_id, project_id = _create_org_and_project(client, owner_headers)

    members = client.get(f"/projects/{project_id}/members", headers=owner_headers).json()

    assert len(members) == 1
    assert members[0]["role"] == "lead"


def test_assignee_must_be_project_member(client: TestClient) -> None:
    owner_headers = register_and_login(client, "task_owner@example.com")
    _org_id, project_id = _create_org_and_project(client, owner_headers)

    # This user is registered but never added to the org/project.
    outsider_user_id = client.post(
        "/auth/register",
        json={"email": "not_a_member@example.com", "password": "secret123", "full_name": "Outsider"},
    ).json()["id"]

    response = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Do something", "assignee_id": outsider_user_id},
        headers=owner_headers,
    )

    assert response.status_code == 400


def test_contributor_cannot_delete_task(client: TestClient) -> None:
    owner_headers = register_and_login(client, "del_owner@example.com")
    org_id, project_id = _create_org_and_project(client, owner_headers)

    contributor_headers = register_and_login(client, "contributor@example.com", "Contributor")
    client.post(
        f"/organizations/{org_id}/members",
        json={"email": "contributor@example.com", "role": "member"},
        headers=owner_headers,
    )
    contributor_user_id = client.get("/users/me", headers=contributor_headers).json()["id"]
    client.post(
        f"/projects/{project_id}/members",
        json={"user_id": contributor_user_id, "role": "contributor"},
        headers=owner_headers,
    )

    task_id = client.post(
        f"/projects/{project_id}/tasks", json={"title": "Fix bug"}, headers=owner_headers
    ).json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers=contributor_headers)

    assert response.status_code == 403


def test_partial_update_only_changes_sent_fields(client: TestClient) -> None:
    owner_headers = register_and_login(client, "patch_owner@example.com")
    _org_id, project_id = _create_org_and_project(client, owner_headers)

    task = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Write docs", "priority": "high"},
        headers=owner_headers,
    ).json()

    response = client.patch(f"/tasks/{task['id']}", json={"status": "in_progress"}, headers=owner_headers)
    updated = response.json()

    assert updated["status"] == "in_progress"
    assert updated["title"] == "Write docs"  # untouched
    assert updated["priority"] == "high"  # untouched
