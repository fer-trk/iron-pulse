import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock
from datetime import date

from app.services import report_service


@pytest.fixture
def mock_session():
    return MagicMock()


def test_get_attendance_summary_report(mock_session):
    mock_session.exec.return_value.one.side_effect = [
        5,  # total_attendances
        3,  # total_check_outs
        2,  # current_people_inside
    ]

    result = report_service.get_attendance_summary_report(
        mock_session,
        start_date=date.today(),
        end_date=date.today(),
    )

    assert result.start_date == date.today()
    assert result.end_date == date.today()
    assert result.total_attendances == 5
    assert result.total_check_ins == 5
    assert result.current_people_inside == 2
    assert result.total_check_outs == 3


def test_get_attendance_summary_invalid_range(mock_session):
    with pytest.raises(HTTPException) as error:
        report_service.get_attendance_summary_report(
            mock_session, start_date=date(2026, 5, 31), end_date=date(2026, 5, 1),
        )
    assert error.value.status_code == 400
    mock_session.exec.assert_not_called()


def test_get_attendance_summary_no_data(mock_session):
    mock_session.exec.return_value.one.side_effect = [
        0,  # total_attendances
        0,  # total_check_ins
        0,  # current_people_inside
    ]

    result = report_service.get_attendance_summary_report(
        mock_session,
        start_date=date.today(),
        end_date=date.today(),
    )

    assert result.total_attendances == 0
    assert result.total_check_ins == 0
    assert result.current_people_inside == 0


def test_get_attendance_by_member_report(mock_session):
    mock_session.exec.return_value.all.return_value = [
        (1, "Ana", "López", 3),
        (2, "Pedro", "Ruiz", 1),
    ]

    result = report_service.get_attendance_by_member_report(
        mock_session,
        start_date=date.today(),
        end_date=date.today(),
    )

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].member_id == 1
    assert result[0].first_name == "Ana"
    assert result[0].total_attendances == 3
    assert result[1].member_id == 2
    assert result[1].total_attendances == 1


def test_get_attendance_by_member_empty_range(mock_session):
    mock_session.exec.return_value.all.return_value = []

    result = report_service.get_attendance_by_member_report(
        mock_session,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 1, 2),
    )

    assert isinstance(result, list)
    assert len(result) == 0


def test_get_attendance_by_reservation_report(mock_session):
    mock_session.exec.return_value.all.return_value = [
        (1, 1, date.today(), 1),
        (2, 2, date.today(), 2),
    ]

    result = report_service.get_attendance_by_reservation_report(
        mock_session,
        start_date=date.today(),
        end_date=date.today(),
    )

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].reservation_id == 1
    assert result[0].member_id == 1
    assert result[0].reservation_date == date.today()
    assert result[0].total_attendances == 1
    assert result[1].reservation_id == 2
    assert result[1].total_attendances == 2


def test_get_attendance_by_reservation_empty_range(mock_session):
    mock_session.exec.return_value.all.return_value = []

    result = report_service.get_attendance_by_reservation_report(
        mock_session,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 1, 2),
    )

    assert isinstance(result, list)
    assert len(result) == 0


def test_get_attendance_by_member_single_result(mock_session):
    mock_session.exec.return_value.all.return_value = [
        (1, "Carlos", "García", 10),
    ]

    result = report_service.get_attendance_by_member_report(
        mock_session,
        start_date=date.today(),
        end_date=date.today(),
    )

    assert len(result) == 1
    assert result[0].total_attendances == 10


def test_get_attendance_by_reservation_single_result(mock_session):
    mock_session.exec.return_value.all.return_value = [
        (5, 3, date.today(), 1),
    ]

    result = report_service.get_attendance_by_reservation_report(
        mock_session,
        start_date=date.today(),
        end_date=date.today(),
    )

    assert len(result) == 1
    assert result[0].reservation_id == 5
    assert result[0].member_id == 3
