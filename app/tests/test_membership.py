from datetime import date, timedelta
from app.models.member import MemberStatus


def test_create_membership(client, auth_headers, active_member, monthly_plan):
    r = client.post("/api/v1/memberships/", json={
        "member_id": active_member.id,
        "plan_id": monthly_plan.id,
        "start_date": str(date.today()),
        "status": "pending",
    }, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["status"] == "pending"


def test_do_not_create_suspended_member(client, auth_headers, session, monthly_plan):
    from app.models.member import Member
    m = Member(first_name="X", last_name="Y", email="xy@gym.es", status=MemberStatus.suspended)
    session.add(m); session.commit(); session.refresh(m)
    r = client.post("/api/v1/memberships/", json={
        "member_id": m.id,
        "plan_id": monthly_plan.id,
        "start_date": str(date.today()),
    }, headers=auth_headers)
    assert r.status_code == 400


def test_renew_membership(client, auth_headers, active_membership):
    r = client.post(f"/api/v1/memberships/{active_membership.id}/renew", headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["status"] == "pending"


def test_expiring_soon(client, auth_headers, active_membership):
    r = client.get("/api/v1/memberships/expiring-soon?days=35", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1

def test_inactive_member_cannot_renew(client, auth_headers, session, active_member, active_membership):
    active_member.is_active = False
    session.add(active_member); session.commit()
    assert client.post(f"/api/v1/memberships/{active_membership.id}/renew").status_code == 400
