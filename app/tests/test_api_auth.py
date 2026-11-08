"""These cases deliberately do not request the auth_headers stub."""

import pytest


from main import app
import re


# Exercise every business operation, including new routes added later.
BUSINESS_OPERATIONS = [
    (method, re.sub(r"\{[^}]+\}", "1", path))
    for path, operations in app.openapi()["paths"].items()
    if path.startswith("/api/v1/") and not path.startswith("/api/v1/auth/")
    for method in operations
    if method in {"get", "post", "patch", "delete", "put"}
]


@pytest.mark.parametrize("method,path", BUSINESS_OPERATIONS)
def test_protected_endpoint_rejects_anonymous_request(client, method, path):
    response = client.request(method, path)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_invalid_token_is_rejected(client):
    response = client.get(
        "/api/v1/members/", headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
