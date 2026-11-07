"""These cases deliberately do not request the auth_headers stub."""

import pytest


@pytest.mark.parametrize("path", [
    "/api/v1/members/",
    "/api/v1/plans/",
    "/api/v1/memberships/",
    "/api/v1/payments/",
    "/api/v1/shifts/",
    "/api/v1/reservations/1",
    "/api/v1/attendances/",
])
def test_protected_endpoint_rejects_anonymous_request(client, path):
    response = client.get(path)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_invalid_token_is_rejected(client):
    response = client.get(
        "/api/v1/members/", headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
