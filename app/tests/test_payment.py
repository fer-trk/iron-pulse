import pytest

from datetime import date
from app.models.membership import Membership, MembershipStatus

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.payment import PaymentMethod, PaymentStatus


pytestmark = pytest.mark.usefixtures("auth_headers")


def test_create_payment(
    client: TestClient,
    session: Session,
    active_membership,
    active_member,
    monthly_plan,
):
    response = client.post(
        "/api/v1/payments/",
        json={
            "membership_id": active_membership.id,
            "amount": str(monthly_plan.price),
            "payment_method": PaymentMethod.card,
            "status": PaymentStatus.completed,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["membership_id"] == active_membership.id
    assert data["payment_method"] == PaymentMethod.card
    assert data["status"] == PaymentStatus.completed


def test_create_payment_cancelled_membership(
    client: TestClient,
    session: Session,
    active_membership,
    monthly_plan,
):
    active_membership.status = MembershipStatus.cancelled
    session.add(active_membership)
    session.commit()

    response = client.post(
        "/api/v1/payments/",
        json={
            "membership_id": active_membership.id,
            "amount": str(monthly_plan.price),
            "payment_method": PaymentMethod.cash,
            "status": PaymentStatus.completed,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot register payments on cancelled memberships"


def test_create_payment_membership_not_found(
    client: TestClient,
    active_member,
    monthly_plan,
):
    response = client.post(
        "/api/v1/payments/",
        json={
            "membership_id": 999,
            "amount": str(monthly_plan.price),
            "payment_method": PaymentMethod.card,
            "status": PaymentStatus.completed,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Membership not found"


def test_get_payment(
    client: TestClient,
    session: Session,
    active_membership,
    active_member,
    monthly_plan,
):
    create_response = client.post(
        "/api/v1/payments/",
        json={
            "membership_id": active_membership.id,
            "amount": str(monthly_plan.price),
            "payment_method": PaymentMethod.transfer,
            "status": PaymentStatus.completed,
        },
    )

    payment_id = create_response.json()["id"]

    response = client.get(f"/api/v1/payments/{payment_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment_id
    assert data["membership_id"] == active_membership.id


def test_get_payment_not_found(client: TestClient):
    response = client.get("/api/v1/payments/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"


def test_list_payments_with_pagination(
    client: TestClient,
    session: Session,
    active_member,
    active_membership,
    monthly_plan,
):
    created_ids = []
    for _ in range(3):
        created = client.post(
            "/api/v1/payments/",
            json={
                "membership_id": active_membership.id,
                "amount": str(monthly_plan.price),
                "payment_method": PaymentMethod.cash,
                "status": PaymentStatus.completed,
            },
        )
        assert created.status_code == 201
        created_ids.append(created.json()["id"])

    response = client.get("/api/v1/payments/?skip=1&limit=2")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2
    assert [p["id"] for p in data] == created_ids[-2::-1]


def test_list_payments_by_membership(
    client: TestClient,
    session: Session,
    active_member,
    active_membership,
    monthly_plan,
):
    client.post(
        "/api/v1/payments/",
        json={
            "membership_id": active_membership.id,
            "amount": str(monthly_plan.price),
            "payment_method": PaymentMethod.card,
            "status": PaymentStatus.completed,
        },
    )

    other_membership = Membership(
        member_id=active_member.id, plan_id=monthly_plan.id,
        start_date=date.today(), status=MembershipStatus.active,
    )
    session.add(other_membership)
    session.commit()
    session.refresh(other_membership)
    other_payment = client.post("/api/v1/payments/", json={
        "membership_id": other_membership.id,
        "amount": "10.00", "payment_method": "cash",
    })
    assert other_payment.status_code == 201

    response = client.get(f"/api/v1/payments/?membership_id={active_membership.id}")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert all(p["membership_id"] == active_membership.id for p in data)


def test_payment_pending_then_completed(
    client: TestClient,
    active_member,
    active_membership,
    monthly_plan,
):
    create_response = client.post(
        "/api/v1/payments/",
        json={
            "membership_id": active_membership.id,
            "amount": str(monthly_plan.price),
            "payment_method": PaymentMethod.card,
            "status": PaymentStatus.pending,
        },
    )

    assert create_response.status_code == 201
    assert create_response.json()["status"] == PaymentStatus.pending

    payment_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/payments/{payment_id}",
        json={"status": PaymentStatus.completed},
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == PaymentStatus.completed
