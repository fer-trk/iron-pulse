import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock
from datetime import datetime

from app.models.member import Member, MemberStatus
from app.schemas.member import MemberCreate, MemberUpdate
from app.services.member import MemberService


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def sample_member():
    return Member(
        id=1,
        first_name="Carlos",
        last_name="García",
        email="carlos@gym.es",
        phone="+34600000001",
        status=MemberStatus.active,
        registration_date=datetime.utcnow(),
    )


def test_create_member(mock_session):
    member_data = MemberCreate(
        first_name="Ana",
        last_name="López",
        email="ana@gym.es",
        phone="+34600111222",
    )
    mock_session.exec.return_value.first.return_value = None
    mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, "id", 1))

    result = MemberService.create(mock_session, member_data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


def test_get_member_found(mock_session, sample_member):
    mock_session.get.return_value = sample_member

    result = MemberService.get_by_id(mock_session, 1)

    assert result == sample_member
    mock_session.get.assert_called_once_with(Member, 1)


def test_get_member_not_found(mock_session):
    mock_session.get.return_value = None

    with pytest.raises(HTTPException) as error:
        MemberService.get_by_id(mock_session, 999)

    assert error.value.status_code == 404
    mock_session.commit.assert_not_called()


def test_get_all_members(mock_session, sample_member):
    mock_session.exec.return_value.all.return_value = [sample_member]

    result = MemberService.get_all(mock_session)

    assert len(result) == 1
    assert result[0].email == "carlos@gym.es"


def test_update_member_found(mock_session, sample_member):
    mock_session.get.return_value = sample_member
    member_data = MemberUpdate(phone="+34611999888")

    result = MemberService.update(mock_session, 1, member_data)

    assert result.phone == "+34611999888"
    assert result.first_name == "Carlos"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_update_member_not_found(mock_session):
    mock_session.get.return_value = None
    member_data = MemberUpdate(phone="+34611999888")

    with pytest.raises(HTTPException) as error:
        MemberService.update(mock_session, 999, member_data)

    assert error.value.status_code == 404
    mock_session.commit.assert_not_called()


def test_deactivate_member_found(mock_session, sample_member):
    mock_session.get.return_value = sample_member

    result = MemberService.update(mock_session, 1, MemberUpdate(is_active=False))

    assert result.is_active is False
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_deactivate_member_not_found(mock_session):
    mock_session.get.return_value = None

    with pytest.raises(HTTPException) as error:
        MemberService.update(mock_session, 999, MemberUpdate(is_active=False))

    assert error.value.status_code == 404
    mock_session.commit.assert_not_called()


def test_reactivate_member_found(mock_session, sample_member):
    sample_member.is_active = False
    mock_session.get.return_value = sample_member

    result = MemberService.update(mock_session, 1, MemberUpdate(is_active=True))

    assert result.is_active is True
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_reactivate_member_not_found(mock_session):
    mock_session.get.return_value = None

    with pytest.raises(HTTPException) as error:
        MemberService.update(mock_session, 999, MemberUpdate(is_active=True))

    assert error.value.status_code == 404
    mock_session.commit.assert_not_called()


def test_delete_member_found(mock_session, sample_member):
    mock_session.get.return_value = sample_member

    mock_session.exec.return_value.first.return_value = None
    result = MemberService.delete(mock_session, 1)

    assert result is None
    mock_session.delete.assert_called_once_with(sample_member)
    mock_session.commit.assert_called_once()


def test_delete_member_not_found(mock_session):
    mock_session.get.return_value = None

    with pytest.raises(HTTPException) as error:
        MemberService.delete(mock_session, 999)

    assert error.value.status_code == 404
    mock_session.commit.assert_not_called()