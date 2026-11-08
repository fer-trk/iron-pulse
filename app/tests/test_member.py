import pytest

from fastapi.testclient import TestClient
from sqlmodel import Session



pytestmark = pytest.mark.usefixtures("auth_headers")


def test_create_member(client: TestClient):
    response = client.post(
        "/api/v1/members/",
        json={
            "first_name": "Ana",
            "last_name": "López",
            "email": "ana.lopez@gym.es",
            "phone": "+34600111222",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["first_name"] == "Ana"
    assert data["last_name"] == "López"
    assert data["email"] == "ana.lopez@gym.es"
    assert data["is_active"] is True


def test_create_member_duplicate_email(client: TestClient):
    payload = {
        "first_name": "Pedro",
        "last_name": "Ruiz",
        "email": "pedro.ruiz@gym.es",
        "phone": "+34600333444",
    }

    first_response = client.post("/api/v1/members/", json=payload)
    second_response = client.post("/api/v1/members/", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email already registered"


def test_get_member(client: TestClient):
    create_response = client.post(
        "/api/v1/members/",
        json={
            "first_name": "Luis",
            "last_name": "Martínez",
            "email": "luis.martinez@gym.es",
            "phone": "+34600555666",
        },
    )

    member_id = create_response.json()["id"]

    response = client.get(f"/api/v1/members/{member_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == member_id
    assert data["first_name"] == "Luis"
    assert data["email"] == "luis.martinez@gym.es"


def test_get_member_not_found(client: TestClient):
    response = client.get("/api/v1/members/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"


def test_list_members_with_pagination(client: TestClient):
    for i in range(3):
        client.post(
            "/api/v1/members/",
            json={
                "first_name": f"Member{i}",
                "last_name": "Test",
                "email": f"member{i}.pagination@gym.es",
                "phone": f"+3460077700{i}",
            },
        )

    response = client.get("/api/v1/members/?skip=1&limit=2")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2
    assert [m["first_name"] for m in data] == ["Member1", "Member2"]


def test_update_member(client: TestClient):
    create_response = client.post(
        "/api/v1/members/",
        json={
            "first_name": "Sofía",
            "last_name": "Fernández",
            "email": "sofia.fernandez@gym.es",
            "phone": "+34600888999",
        },
    )

    member_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/members/{member_id}",
        json={"phone": "+34611000111"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["phone"] == "+34611000111"
    assert data["first_name"] == "Sofía"


def test_update_member_not_found(client: TestClient):
    response = client.patch(
        "/api/v1/members/999",
        json={"phone": "+34611000111"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"


def test_deactivate_member(client: TestClient):
    create_response = client.post(
        "/api/v1/members/",
        json={
            "first_name": "Miguel",
            "last_name": "Torres",
            "email": "miguel.torres@gym.es",
            "phone": "+34600121212",
        },
    )

    member_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/members/{member_id}", json={"is_active": False})

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_deactivate_member_not_found(client: TestClient):
    response = client.patch("/api/v1/members/999", json={"is_active": False})

    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"


def test_reactivate_member(client: TestClient, session: Session):
    from app.models.member import Member

    member = Member(
        first_name="Inactivo",
        last_name="Test",
        email="inactivo.test@gym.es",
        phone="+34600131313",
        is_active=False,
    )
    session.add(member)
    session.commit()
    session.refresh(member)

    response = client.patch(f"/api/v1/members/{member.id}", json={"is_active": True})

    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_delete_member(client: TestClient):
    create_response = client.post(
        "/api/v1/members/",
        json={
            "first_name": "Borrar",
            "last_name": "Me",
            "email": "borrar.me@gym.es",
            "phone": "+34600141414",
        },
    )

    member_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/members/{member_id}")

    assert response.status_code == 204

    get_response = client.get(f"/api/v1/members/{member_id}")

    assert get_response.status_code == 404


def test_delete_member_not_found(client: TestClient):
    response = client.delete("/api/v1/members/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"
