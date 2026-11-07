import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock
from datetime import date, datetime

from app.models.attendance import Attendance
from app.models.member import Member
from app.models.reservation import Reservation, ReservationStatus
from app.schemas.attendance import AttendanceCreate
from app.services import attendance_service


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def sample_member():
    return Member(
        id=1,
        first_name="Test",
        last_name="Member",
        email="test.member@gym.es",
        phone="600000000",
        is_active=True,
    )


@pytest.fixture
def sample_reservation():
    return Reservation(
        id=1,
        member_id=1,
        shift_id=None,
        date=date.today(),
        status=ReservationStatus.confirmed,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_attendance():
    return Attendance(
        id=1,
        member_id=1,
        reservation_id=1,
        check_in=datetime.utcnow(),
        check_out=None,
    )


def test_create_attendance_success(mock_session, sample_member, sample_reservation):
    mock_session.get.side_effect = lambda model, id: (
        sample_member if model == Member else sample_reservation
    )
    mock_session.exec.return_value.first.return_value = None
    mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, "id", 1))

    attendance_data = AttendanceCreate(member_id=1, reservation_id=1)

    result = attendance_service.create_attendance(mock_session, attendance_data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


def test_create_attendance_member_not_found(mock_session):
    mock_session.get.side_effect = lambda model, id: None

    attendance_data = AttendanceCreate(member_id=999, reservation_id=1)

    with pytest.raises(HTTPException) as error:
        attendance_service.create_attendance(mock_session, attendance_data)

    assert error.value.status_code == 404
    mock_session.commit.assert_not_called()


def test_create_attendance_reservation_not_found(mock_session, sample_member):
    mock_session.get.side_effect = lambda model, id: (
        sample_member if model == Member else None
    )

    attendance_data = AttendanceCreate(member_id=1, reservation_id=999)

    with pytest.raises(HTTPException) as error:
        attendance_service.create_attendance(mock_session, attendance_data)

    assert error.value.status_code == 404
    mock_session.commit.assert_not_called()


def test_create_attendance_wrong_member(mock_session, sample_member):
    reservation = Reservation(
        id=1,
        member_id=2,
        shift_id=None,
        date=date.today(),
        status=ReservationStatus.confirmed,
    )
    mock_session.get.side_effect = lambda model, id: (
        sample_member if model == Member else reservation
    )

    attendance_data = AttendanceCreate(member_id=1, reservation_id=1)

    with pytest.raises(HTTPException) as error:
        attendance_service.create_attendance(mock_session, attendance_data)

    assert error.value.status_code == 400
    mock_session.commit.assert_not_called()


def test_create_attendance_cancelled_reservation(mock_session, sample_member):
    reservation = Reservation(
        id=1,
        member_id=1,
        shift_id=None,
        date=date.today(),
        status=ReservationStatus.cancelled,
    )
    mock_session.get.side_effect = lambda model, id: (
        sample_member if model == Member else reservation
    )

    attendance_data = AttendanceCreate(member_id=1, reservation_id=1)

    with pytest.raises(HTTPException) as error:
        attendance_service.create_attendance(mock_session, attendance_data)

    assert error.value.status_code == 400
    mock_session.commit.assert_not_called()


def test_create_attendance_duplicate(
    mock_session,
    sample_member,
    sample_reservation,
    sample_attendance,
):
    mock_session.get.side_effect = lambda model, id: (
        sample_member if model == Member else sample_reservation
    )
    mock_session.exec.return_value.first.return_value = sample_attendance

    attendance_data = AttendanceCreate(member_id=1, reservation_id=1)

    with pytest.raises(HTTPException) as error:
        attendance_service.create_attendance(mock_session, attendance_data)

    assert error.value.status_code == 409
    mock_session.commit.assert_not_called()


def test_get_attendance_found(mock_session, sample_attendance):
    mock_session.get.return_value = sample_attendance

    result = attendance_service.get_attendance_by_id(mock_session, 1)

    assert result == sample_attendance
    mock_session.get.assert_called_once_with(Attendance, 1)


def test_get_attendance_not_found(mock_session):
    mock_session.get.return_value = None

    with pytest.raises(HTTPException) as error:
        attendance_service.get_attendance_by_id(mock_session, 999)

    assert error.value.status_code == 404
    mock_session.commit.assert_not_called()


def test_get_all_attendances(mock_session, sample_attendance):
    mock_session.exec.return_value.all.return_value = [sample_attendance]

    result = attendance_service.get_attendances(mock_session)

    assert len(result) == 1
    assert result[0].member_id == 1


def test_register_check_out_success(mock_session, sample_attendance):
    mock_session.get.return_value = sample_attendance

    result = attendance_service.register_check_out(mock_session, 1)

    assert result.check_out is not None
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_register_check_out_not_found(mock_session):
    mock_session.get.return_value = None

    with pytest.raises(HTTPException) as error:
        attendance_service.register_check_out(mock_session, 999)

    assert error.value.status_code == 404
    mock_session.commit.assert_not_called()


def test_register_check_out_already_checked_out(mock_session):
    attendance = Attendance(
        id=1,
        member_id=1,
        reservation_id=1,
        check_in=datetime.utcnow(),
        check_out=datetime.utcnow(),
    )
    mock_session.get.return_value = attendance

    with pytest.raises(HTTPException) as error:
        attendance_service.register_check_out(mock_session, 1)

    assert error.value.status_code == 409
    mock_session.commit.assert_not_called()
