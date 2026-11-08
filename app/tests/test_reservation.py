from datetime import date, timedelta
import pytest
from app.models.member import Member
from app.models.membership import Membership, MembershipStatus

pytestmark = pytest.mark.usefixtures("auth_headers")


@pytest.fixture
def enrollment_data(client, session, active_membership, active_member):
    day = date.today() + timedelta(days=1)
    response = client.post("/api/v1/shifts/", json={
        "class_name": "Yoga", "instructor": "Ana", "day_of_week": day.strftime("%A").lower(),
        "start_time": "09:00", "end_time": "10:00", "max_capacity": 1,
    })
    assert response.status_code == 201
    return {"member_id": active_member.id, "shift_id": response.json()["id"], "date": str(day)}


def test_enrollment_uses_selected_member_not_staff_id(client, session, active_membership, enrollment_data):
    member = Member(first_name="Other", last_name="Member", email="other@example.com")
    session.add(member); session.commit(); session.refresh(member)
    session.add(Membership(member_id=member.id, plan_id=active_membership.plan_id,
                           start_date=date.today(), end_date=active_membership.end_date, status=MembershipStatus.active))
    session.commit()
    data = {**enrollment_data, "member_id": member.id}
    response = client.post("/api/v1/reservations/", json=data)
    assert response.status_code == 201
    assert response.json()["member_id"] == member.id
    assert member.id != 1


def test_duplicate_capacity_cancel_and_reenroll(client, enrollment_data):
    first = client.post("/api/v1/reservations/", json=enrollment_data)
    assert first.status_code == 201
    assert client.post("/api/v1/reservations/", json=enrollment_data).status_code == 409
    enrollment = first.json()["id"]
    assert client.patch(f"/api/v1/reservations/{enrollment}/cancel").status_code == 200
    again = client.post("/api/v1/reservations/", json=enrollment_data)
    assert again.status_code == 201
    assert again.json()["id"] == enrollment
    assert len(client.get("/api/v1/reservations/").json()) == 1


def test_paid_membership_required(client, session, active_membership, enrollment_data):
    active_membership.status = MembershipStatus.pending
    session.add(active_membership); session.commit()
    assert client.post("/api/v1/reservations/", json=enrollment_data).status_code == 400


@pytest.mark.parametrize("case", ["inactive-member", "inactive-shift", "wrong-day", "past-day", "expired-membership"])
def test_invalid_enrollment(client, session, active_member, active_membership, enrollment_data, case):
    from app.models.shift import AvailableShift
    if case == "inactive-member":
        active_member.is_active = False; session.add(active_member)
    elif case == "inactive-shift":
        shift = session.get(AvailableShift, enrollment_data["shift_id"]); shift.active_slot = False; session.add(shift)
    elif case == "wrong-day":
        enrollment_data["date"] = str(date.fromisoformat(enrollment_data["date"]) + timedelta(days=1))
    elif case == "past-day":
        enrollment_data["date"] = str(date.today() - timedelta(days=1))
    else:
        active_membership.end_date = date.today() - timedelta(days=1); session.add(active_membership)
    session.commit()
    response = client.post("/api/v1/reservations/", json=enrollment_data)
    assert response.status_code == (422 if case == "past-day" else 400)


def test_full_class_rejects_another_member(client, session, active_membership, enrollment_data):
    assert client.post("/api/v1/reservations/", json=enrollment_data).status_code == 201
    member = Member(first_name="Second", last_name="Member", email="second@example.com")
    session.add(member); session.commit(); session.refresh(member)
    session.add(Membership(member_id=member.id, plan_id=active_membership.plan_id, start_date=date.today(), end_date=active_membership.end_date, status=MembershipStatus.active)); session.commit()
    assert client.post("/api/v1/reservations/", json={**enrollment_data, "member_id": member.id}).status_code == 409


def test_deletion_keeps_enrollment_history(client, enrollment_data):
    assert client.post("/api/v1/reservations/", json=enrollment_data).status_code == 201
    assert client.delete(f"/api/v1/shifts/{enrollment_data['shift_id']}").status_code == 400
    assert client.delete(f"/api/v1/members/{enrollment_data['member_id']}").status_code == 400


def test_schedule_cannot_change_with_confirmed_enrollments(client, enrollment_data):
    assert client.post("/api/v1/reservations/", json=enrollment_data).status_code == 201
    assert client.patch(f"/api/v1/shifts/{enrollment_data['shift_id']}", json={"start_time":"08:00"}).status_code == 400
