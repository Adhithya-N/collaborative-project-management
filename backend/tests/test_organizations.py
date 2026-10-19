"""Tests for organizations, membership, and role-based access control."""

from fastapi.testclient import TestClient

from tests.conftest import register_and_login as _register_and_login


def test_creating_an_org_makes_creator_the_owner(client: TestClient) -> None:
    headers = _register_and_login(client, "owner@example.com")

    create_response = client.post(
        "/organizations", json={"name": "Acme Corp", "slug": "acme-corp"}, headers=headers
    )
    assert create_response.status_code == 201
    org_id = create_response.json()["id"]

    members_response = client.get(f"/organizations/{org_id}/members", headers=headers)
    members = members_response.json()

    assert len(members) == 1
    assert members[0]["role"] == "owner"


def test_member_cannot_invite_others(client: TestClient) -> None:
    owner_headers = _register_and_login(client, "owner2@example.com")
    org_id = client.post(
        "/organizations", json={"name": "Beta Inc", "slug": "beta-inc"}, headers=owner_headers
    ).json()["id"]

    member_headers = _register_and_login(client, "member2@example.com", "Member Two")
    client.post(
        f"/organizations/{org_id}/members",
        json={"email": "member2@example.com", "role": "member"},
        headers=owner_headers,
    )

    # The member tries to invite a third person - this must be blocked.
    response = client.post(
        f"/organizations/{org_id}/members",
        json={"email": "someone@example.com", "role": "member"},
        headers=member_headers,
    )

    assert response.status_code == 403


def test_non_member_cannot_view_org_members(client: TestClient) -> None:
    owner_headers = _register_and_login(client, "owner3@example.com")
    org_id = client.post(
        "/organizations", json={"name": "Gamma LLC", "slug": "gamma-llc"}, headers=owner_headers
    ).json()["id"]

    outsider_headers = _register_and_login(client, "outsider@example.com")

    response = client.get(f"/organizations/{org_id}/members", headers=outsider_headers)

    assert response.status_code == 403
