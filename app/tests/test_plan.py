import pytest

pytestmark = pytest.mark.usefixtures("auth_headers")


def test_create_plan(client):
    response = client.post("/api/v1/plans/", json={
        "name": "Basic", "price": 29.99, "duration_days": 30,
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Basic"
    assert response.json()["price"] == 29.99
    assert response.json()["active"] is True


def test_duplicate_plan_name(client, monthly_plan):
    response = client.post("/api/v1/plans/", json={
        "name": monthly_plan.name, "price": 10,
    })
    assert response.status_code == 409


@pytest.mark.parametrize("field,value", [("price", -1), ("duration_days", 0)])
def test_invalid_plan(client, field, value):
    response = client.post("/api/v1/plans/", json={
        "name": "Invalid", "price": 10, field: value,
    })
    assert response.status_code == 422


def test_get_plan(client, monthly_plan):
    response = client.get(f"/api/v1/plans/{monthly_plan.id}")
    assert response.status_code == 200
    assert response.json()["id"] == monthly_plan.id
    assert response.json()["name"] == monthly_plan.name


def test_get_plan_not_found(client):
    response = client.get("/api/v1/plans/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Plan not found"


def test_list_active_plans(client, session, monthly_plan):
    from app.models.plan import Plan
    session.add(Plan(name="Retired", price=10, active=False))
    session.commit()
    response = client.get("/api/v1/plans/?active=true")
    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == [monthly_plan.id]


def test_update_plan(client, monthly_plan):
    response = client.patch(f"/api/v1/plans/{monthly_plan.id}", json={"price": 35})
    assert response.status_code == 200
    assert response.json()["price"] == 35
    assert response.json()["name"] == monthly_plan.name


def test_update_plan_not_found(client):
    assert client.patch("/api/v1/plans/999", json={"price": 35}).status_code == 404


def test_delete_plan(client, monthly_plan):
    response = client.delete(f"/api/v1/plans/{monthly_plan.id}")
    assert response.status_code == 200
    assert client.get(f"/api/v1/plans/{monthly_plan.id}").status_code == 404


def test_delete_plan_with_memberships_is_rejected(client, monthly_plan, active_membership):
    response = client.delete(f"/api/v1/plans/{monthly_plan.id}")
    assert response.status_code == 400
    assert client.get(f"/api/v1/plans/{monthly_plan.id}").status_code == 200


def test_delete_plan_not_found(client):
    assert client.delete("/api/v1/plans/999").status_code == 404
