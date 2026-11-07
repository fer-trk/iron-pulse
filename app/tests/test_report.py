from datetime import date
import pytest

pytestmark = pytest.mark.usefixtures("auth_headers")

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.attendance import Attendance
from app.models.member import Member
from app.models.reservation import Reservation, ReservationStatus


def test_get_attendance_summary_report(
    client: TestClient,
    session: Session,
):
    member = Member(
        first_name="Report",
        last_name="Summary",
        email="report.summary@example.com",
        phone="600100100",
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

    attendance = Attendance(
        member_id=member.id,
        reservation_id=reservation.id,
    )
    session.add(attendance)
    session.commit()
    session.refresh(attendance)

    response = client.get(
        f"/api/v1/reports/attendance?start_date={date.today()}&end_date={date.today()}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["start_date"] == date.today().isoformat()
    assert data["end_date"] == date.today().isoformat()
    assert data["total_attendances"] >= 1
    assert data["total_check_ins"] >= 1
    assert data["current_people_inside"] >= 1


def test_get_attendance_by_member_report(
    client: TestClient,
    session: Session,
):
    member = Member(
        first_name="Report",
        last_name="Member",
        email="report.member@example.com",
        phone="600100101",
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

    attendance = Attendance(
        member_id=member.id,
        reservation_id=reservation.id,
    )
    session.add(attendance)
    session.commit()
    session.refresh(attendance)

    response = client.get(
        f"/api/v1/reports/attendance/by-member?start_date={date.today()}&end_date={date.today()}"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    member_report = next(
        item for item in data if item["member_id"] == member.id
    )

    assert member_report["first_name"] == member.first_name
    assert member_report["last_name"] == member.last_name
    assert member_report["total_attendances"] >= 1


def test_get_attendance_by_reservation_report(
    client: TestClient,
    session: Session,
):
    member = Member(
        first_name="Report",
        last_name="Reservation",
        email="report.reservation@example.com",
        phone="600100102",
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

    attendance = Attendance(
        member_id=member.id,
        reservation_id=reservation.id,
    )
    session.add(attendance)
    session.commit()
    session.refresh(attendance)

    response = client.get(
        f"/api/v1/reports/attendance/by-reservation?start_date={date.today()}&end_date={date.today()}"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    reservation_report = next(
        item for item in data if item["reservation_id"] == reservation.id
    )

    assert reservation_report["member_id"] == member.id
    assert reservation_report["reservation_date"] == date.today().isoformat()
    assert reservation_report["total_attendances"] >= 1


def test_attendance_report_invalid_date_range(
    client: TestClient,
):
    response = client.get(
        "/api/v1/reports/attendance?start_date=2026-05-31&end_date=2026-05-01"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "start_date cannot be greater than end_date"

