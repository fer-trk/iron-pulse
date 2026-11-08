from datetime import date
from decimal import Decimal
import pytest
from app.models.membership import MembershipStatus

pytestmark = pytest.mark.usefixtures("auth_headers")


@pytest.fixture
def pending(client, active_member, monthly_plan):
    response = client.post("/api/v1/memberships/", json={
        "member_id": active_member.id, "plan_id": monthly_plan.id,
        "start_date": str(date.today()),
    })
    assert response.status_code == 201
    return response.json()["id"]


def pay(client, membership, amount="49.99", status="completed"):
    return client.post("/api/v1/payments/", json={
        "membership_id": membership, "amount": amount,
        "payment_method": "cash", "status": status,
    })


def state(client, membership):
    return client.get(f"/api/v1/memberships/{membership}").json()["status"]


def test_exact_price_activates_membership(client, pending):
    assert pay(client, pending).status_code == 201
    assert state(client, pending) == "active"


def test_partial_payments_only_activate_at_full_balance(client, pending):
    assert pay(client, pending, "20.00").status_code == 201
    assert state(client, pending) == "pending"
    assert pay(client, pending, "29.99").status_code == 201
    assert state(client, pending) == "active"


def test_completing_and_refunding_payment_recalculates_balance(client, pending):
    payment = pay(client, pending, status="pending").json()["id"]
    assert state(client, pending) == "pending"
    response = client.patch(f"/api/v1/payments/{payment}", json={"status": "completed"})
    assert response.status_code == 200
    assert state(client, pending) == "active"
    assert client.patch(f"/api/v1/payments/{payment}", json={"status": "refunded"}).status_code == 200
    assert state(client, pending) == "pending"


def test_deleting_completed_payment_recalculates_balance(client, pending):
    payment = pay(client, pending).json()["id"]
    assert client.delete(f"/api/v1/payments/{payment}").status_code == 204
    assert state(client, pending) == "pending"


def test_null_amount_uses_plan_price(client, pending):
    response = pay(client, pending, None)
    assert response.status_code == 201
    assert Decimal(response.json()["amount"]) == Decimal("49.99")
    assert state(client, pending) == "active"


@pytest.mark.parametrize("amount", ["-1", "0", "1.001", "1000000", "NaN"])
def test_invalid_amount_is_rejected(client, pending, amount):
    assert pay(client, pending, amount).status_code == 422
    assert state(client, pending) == "pending"


def test_inactive_member_cannot_get_membership(client, session, active_member, monthly_plan):
    active_member.is_active = False
    session.add(active_member)
    session.commit()
    response = client.post("/api/v1/memberships/", json={
        "member_id": active_member.id, "plan_id": monthly_plan.id, "start_date": str(date.today()),
    })
    assert response.status_code == 400


def test_unpaid_membership_cannot_be_manually_activated(client, pending):
    assert client.patch(f"/api/v1/memberships/{pending}", json={"status": "active"}).status_code == 400
    assert state(client, pending) == "pending"


def test_membership_with_pending_payment_cannot_be_deleted(client, pending):
    assert pay(client, pending, status="pending").status_code == 201
    assert client.delete(f"/api/v1/memberships/{pending}").status_code == 400
    assert state(client, pending) == "pending"
