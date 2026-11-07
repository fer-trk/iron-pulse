import pytest

from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.member import Member
from app.models.reservation import Reservation, ReservationStatus


pytestmark = pytest.mark.usefixtures("auth_headers")


def test_register_attendance_success(
    client: TestClient,
    session: Session,
):
    member = Member(
        first_name="Test",
        last_name="Member",
        email="test.member@example.com",
        phone="600000000",
        is_active=True,
    )
    session.add(member)
    session.commit()
    session.refresh(member)

    reservation = Reservation(
        member_id=member.id,
        shift_id=None,
        date=date.today(),
        status=ReservationStatus.confirmed,
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)

    response = client.post(
        "/api/v1/attendances/",
        json={
            "member_id": member.id,
            "reservation_id": reservation.id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["member_id"] == member.id
    assert data["reservation_id"] == reservation.id
    assert data["check_in"] is not None
    assert data["check_out"] is None


def test_register_attendance_member_not_found(
    client: TestClient,
):
    response = client.post(
        "/api/v1/attendances/",
        json={
            "member_id": 999,
            "reservation_id": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"


def test_register_attendance_reservation_not_found(
    client: TestClient,
    session: Session,
):
    member = Member(
        first_name="Test",
        last_name="Member",
        email="reservation.notfound@example.com",
        phone="600000001",
        is_active=True,
    )
    session.add(member)
    session.commit()
    session.refresh(member)

    response = client.post(
        "/api/v1/attendances/",
        json={
            "member_id": member.id,
            "reservation_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Reservation not found"


def test_register_attendance_reservation_does_not_belong_to_member(
    client: TestClient,
    session: Session,
):
    member_1 = Member(
        first_name="First",
        last_name="Member",
        email="first.member@example.com",
        phone="600000002",
        is_active=True,
    )
    member_2 = Member(
        first_name="Second",
        last_name="Member",
        email="second.member@example.com",
        phone="600000003",
        is_active=True,
    )

    session.add(member_1)
    session.add(member_2)
    session.commit()
    session.refresh(member_1)
    session.refresh(member_2)

    reservation = Reservation(
        member_id=member_2.id,
        shift_id=None,
        date=date.today(),
        status=ReservationStatus.confirmed,
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)

    response = client.post(
        "/api/v1/attendances/",
        json={
            "member_id": member_1.id,
            "reservation_id": reservation.id,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Reservation does not belong to this member"


def test_register_attendance_for_cancelled_reservation(
    client: TestClient,
    session: Session,
):
    member = Member(
        first_name="Cancelled",
        last_name="Reservation",
        email="cancelled.reservation@example.com",
        phone="600000004",
        is_active=True,
    )
    session.add(member)
    session.commit()
    session.refresh(member)

    reservation = Reservation(
        member_id=member.id,
        shift_id=None,
        date=date.today(),
        status=ReservationStatus.cancelled,
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)

    response = client.post(
        "/api/v1/attendances/",
        json={
            "member_id": member.id,
            "reservation_id": reservation.id,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Attendance can only be registered for confirmed reservations"
    )


def test_register_duplicate_attendance(
    client: TestClient,
    session: Session,
):
    member = Member(
        first_name="Duplicate",
        last_name="Attendance",
        email="duplicate.attendance@example.com",
        phone="600000005",
        is_active=True,
    )
    session.add(member)
    session.commit()
    session.refresh(member)

    reservation = Reservation(
        member_id=member.id,
        shift_id=None,
        date=date.today(),
        status=ReservationStatus.confirmed,
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)

    payload = {
        "member_id": member.id,
        "reservation_id": reservation.id,
    }

    first_response = client.post("/api/v1/attendances/", json=payload)
    second_response = client.post("/api/v1/attendances/", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Attendance already registered for this member and reservation"
    )


def test_list_attendances_with_pagination(
    client: TestClient,
    session: Session,
):
    member = Member(
        first_name="List",
        last_name="Attendance",
        email="list.attendance@example.com",
        phone="600000006",
        is_active=True,
    )
    session.add(member)
    session.commit()
    session.refresh(member)

    for index in range(3):
        reservation = Reservation(
            member_id=member.id,
            shift_id=None,
            date=date.today(),
            status=ReservationStatus.confirmed,
        )
        session.add(reservation)
        session.commit()
        session.refresh(reservation)

        client.post(
            "/api/v1/attendances/",
            json={
                "member_id": member.id,
                "reservation_id": reservation.id,
            },
        )

    response = client.get("/api/v1/attendances/?offset=0&limit=2")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2


def test_get_attendance_by_id(
    client: TestClient,
    session: Session,
):
    member = Member(
        first_name="Detail",
        last_name="Attendance",
        email="detail.attendance@example.com",
        phone="600000007",
        is_active=True,
    )
    session.add(member)
    session.commit()
    session.refresh(member)

    reservation = Reservation(
        member_id=member.id,
        shift_id=None,
        date=date.today(),
        status=ReservationStatus.confirmed,
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)

    create_response = client.post(
        "/api/v1/attendances/",
        json={
            "member_id": member.id,
            "reservation_id": reservation.id,
        },
    )

    attendance_id = create_response.json()["id"]

    response = client.get(f"/api/v1/attendances/{attendance_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == attendance_id
    assert data["member_id"] == member.id
    assert data["reservation_id"] == reservation.id


def test_register_check_out_success(
    client: TestClient,
    session: Session,
):
    member = Member(
        first_name="Check",
        last_name="Out",
        email="check.out@example.com",
        phone="600000008",
        is_active=True,
    )
    session.add(member)
    session.commit()
    session.refresh(member)

    reservation = Reservation(
        member_id=member.id,
        shift_id=None,
        date=date.today(),
        status=ReservationStatus.confirmed,
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)

    create_response = client.post(
        "/api/v1/attendances/",
        json={
            "member_id": member.id,
            "reservation_id": reservation.id,
        },
    )

    attendance_id = create_response.json()["id"]

    response = client.post(f"/api/v1/attendances/{attendance_id}/check-out")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == attendance_id
    assert data["check_out"] is not None


def test_register_check_out_twice(
    client: TestClient,
    session: Session,
):
    member = Member(
        first_name="Double",
        last_name="Checkout",
        email="double.checkout@example.com",
        phone="600000009",
        is_active=True,
    )
    session.add(member)
    session.commit()
    session.refresh(member)

    reservation = Reservation(
        member_id=member.id,
        shift_id=None,
        date=date.today(),
        status=ReservationStatus.confirmed,
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)

    create_response = client.post(
        "/api/v1/attendances/",
        json={
            "member_id": member.id,
            "reservation_id": reservation.id,
        },
    )

    attendance_id = create_response.json()["id"]

    first_response = client.post(f"/api/v1/attendances/{attendance_id}/check-out")
    second_response = client.post(f"/api/v1/attendances/{attendance_id}/check-out")

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Check-out already registered for this attendance"
    )
    