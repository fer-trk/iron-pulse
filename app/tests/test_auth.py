"""Authentication and account creation exercised without dependency stubs."""

from datetime import datetime, timedelta, timezone

from jose import jwt
import pytest
from sqlmodel import select

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import User


PASSWORD = "Educational-password-2026!"


@pytest.fixture(scope="module")
def stored_hash():
    return hash_password(PASSWORD)


@pytest.fixture
def make_user(session, stored_hash):
    def create(username="staff", is_admin=False, is_active=True):
        user = User(username=username, hashed_password=stored_hash,
                    is_admin=is_admin, is_active=is_active)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    return create


def headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def test_login_and_access_business_route(client, make_user):
    user = make_user()
    response = client.post("/api/v1/auth/token", data={"username": user.username, "password": PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    claims = jwt.decode(body["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert claims["sub"] == str(user.id)
    assert claims["type"] == "access"
    assert claims["exp"] > datetime.now(timezone.utc).timestamp()
    assert claims["jti"]
    result = client.get("/api/v1/members/", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert result.status_code == 200
    assert result.json() == []


@pytest.mark.parametrize("case", ["wrong-password", "unknown-user", "inactive-user"])
def test_login_rejects_invalid_credentials(client, make_user, case):
    make_user(is_active=case != "inactive-user")
    response = client.post("/api/v1/auth/token", data={
        "username": "unknown" if case == "unknown-user" else "staff",
        "password": "wrong-password" if case == "wrong-password" else PASSWORD,
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("case", [
    "expired", "tampered", "missing-exp", "missing-sub", "missing-type",
    "refresh", "invalid-sub", "zero-sub", "negative-sub", "oversized-sub", "unknown-user",
])
def test_unusable_token_is_rejected(client, make_user, case):
    user = make_user()
    claims = {"sub": str(user.id), "exp": datetime.now(timezone.utc) + timedelta(minutes=5), "type": "access"}
    key = settings.SECRET_KEY
    if case == "expired":
        claims["exp"] = datetime.now(timezone.utc) - timedelta(minutes=5)
    elif case == "tampered":
        key = "different-signing-key-for-the-negative-test"
    elif case.startswith("missing-"):
        claims.pop(case.removeprefix("missing-"))
    elif case == "refresh":
        claims["type"] = "refresh"
    elif case == "invalid-sub":
        claims["sub"] = "not-a-user-id"
    elif case == "zero-sub":
        claims["sub"] = "0"
    elif case == "negative-sub":
        claims["sub"] = "-1"
    elif case == "oversized-sub":
        claims["sub"] = str(2 ** 63)
    elif case == "unknown-user":
        claims["sub"] = "999"
    token = jwt.encode(claims, key, algorithm=settings.ALGORITHM)
    response = client.get("/api/v1/members/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


@pytest.mark.parametrize("operation", ["deactivate", "delete"])
def test_existing_token_stops_working_when_account_changes(client, session, make_user, operation):
    user = make_user()
    auth = headers(user)
    assert client.get("/api/v1/members/", headers=auth).status_code == 200
    if operation == "deactivate":
        user.is_active = False
        session.add(user)
    else:
        session.delete(user)
    session.commit()
    assert client.get("/api/v1/members/", headers=auth).status_code == 401


def test_anonymous_cannot_create_admin(client, session):
    response = client.post("/api/v1/auth/register", json={
        "username": "intruder", "password": PASSWORD, "is_admin": True,
    })
    assert response.status_code == 401
    assert session.exec(select(User)).all() == []


def test_staff_cannot_create_admin(client, session, make_user):
    user = make_user()
    response = client.post("/api/v1/auth/register", headers=headers(user), json={
        "username": "intruder", "password": PASSWORD, "is_admin": True,
    })
    assert response.status_code == 403
    assert len(session.exec(select(User)).all()) == 1


@pytest.mark.parametrize("is_admin", [False, True])
def test_admin_can_create_accounts(client, session, make_user, is_admin):
    admin = make_user("administrator", is_admin=True)
    response = client.post("/api/v1/auth/register", headers=headers(admin), json={
        "username": " new-user ", "password": PASSWORD, "is_admin": is_admin,
    })
    assert response.status_code == 201
    assert response.json()["username"] == "new-user"
    assert response.json()["is_admin"] is is_admin
    assert response.json()["is_active"] is True
    assert "password" not in response.json()
    assert "hashed_password" not in response.json()
    created = session.exec(select(User).where(User.username == "new-user")).one()
    assert created.hashed_password != PASSWORD
    assert verify_password(PASSWORD, created.hashed_password)
    login = client.post("/api/v1/auth/token", data={"username": "new-user", "password": PASSWORD})
    assert login.status_code == 200


def test_duplicate_username_is_rejected(client, make_user):
    admin = make_user("administrator", is_admin=True)
    response = client.post("/api/v1/auth/register", headers=headers(admin), json={
        "username": "administrator", "password": PASSWORD,
    })
    assert response.status_code == 409


@pytest.mark.parametrize("changes", [
    {"username": " "}, {"username": "x" * 101}, {"password": "short"},
    {"password": "x" * 73}, {"password": "é" * 37}, {"is_active": False},
])
def test_invalid_account_payload_is_rejected(client, session, make_user, changes):
    admin = make_user("administrator", is_admin=True)
    response = client.post("/api/v1/auth/register", headers=headers(admin), json={
        "username": "new-user", "password": PASSWORD, **changes,
    })
    assert response.status_code == 422
    assert len(session.exec(select(User)).all()) == 1


def test_admin_permission_is_read_from_database(client, session, make_user):
    admin = make_user("administrator", is_admin=True)
    auth = headers(admin)
    admin.is_admin = False
    session.add(admin)
    session.commit()
    response = client.post("/api/v1/auth/register", headers=auth,
                           json={"username": "other", "password": PASSWORD})
    assert response.status_code == 403


def test_bcrypt_hashing_and_bad_passwords(stored_hash):
    assert stored_hash.startswith("$2b$")
    assert verify_password(PASSWORD, stored_hash)
    assert not verify_password("different-password", stored_hash)
    assert not verify_password("x" * 73, stored_hash)
    assert not verify_password(PASSWORD, "not-a-hash")


def test_tokens_have_distinct_session_identifiers():
    assert create_access_token(1) != create_access_token(1)


def test_refresh_token_cannot_access_business_routes(client, make_user):
    user = make_user()
    response = client.get("/api/v1/members/", headers={
        "Authorization": f"Bearer {create_refresh_token(user.id)}",
    })
    assert response.status_code == 401


def test_logout_requires_a_valid_user(client):
    assert client.post("/api/v1/auth/logout").status_code == 401
    assert client.post("/api/v1/auth/logout", headers={"Authorization": "Bearer invalid"}).status_code == 401


@pytest.mark.parametrize("legacy_hash", [
    "$2a$12$GhvMmNVjRW29ulnudl.LbuAnUtN/LRfe1JsBm1Xu6LE3059z5Tr8m",
    "$2b$12$GhvMmNVjRW29ulnudl.LbuAnUtN/LRfe1JsBm1Xu6LE3059z5Tr8m",
])
def test_hashes_from_passlib_documentation_remain_valid(legacy_hash):
    # Public BCrypt vector from Passlib, also exercised with its 2a identifier.
    # https://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt.html
    assert verify_password("password", legacy_hash)
    assert not verify_password("incorrect", legacy_hash)


def test_initial_admin_is_hashed_and_can_log_in(client, session):
    from app.scripts.create_admin import create_initial_admin
    from app.schemas.user import UserCreate
    user = create_initial_admin(session, UserCreate(username="initial-admin", password=PASSWORD))
    assert user.is_admin and user.is_active
    assert user.hashed_password != PASSWORD
    response = client.post("/api/v1/auth/token", data={"username": user.username, "password": PASSWORD})
    assert response.status_code == 200


def test_initial_admin_does_not_overwrite_staff(session, make_user):
    from app.scripts.create_admin import create_initial_admin
    from app.schemas.user import UserCreate
    user = make_user()
    with pytest.raises(ValueError, match="never promoted or overwritten"):
        create_initial_admin(session, UserCreate(username=user.username, password=PASSWORD))
    session.refresh(user)
    assert not user.is_admin
    assert len(session.exec(select(User)).all()) == 1


def test_initial_admin_cannot_be_created_twice(session, make_user):
    from app.scripts.create_admin import create_initial_admin
    from app.schemas.user import UserCreate
    make_user("initial-admin", is_admin=True)
    with pytest.raises(ValueError, match="administrator already exists"):
        create_initial_admin(session, UserCreate(username="second-admin", password=PASSWORD))
    assert len(session.exec(select(User)).all()) == 1


def test_bootstrap_cli_does_not_print_password(session, monkeypatch, capsys):
    from app.scripts import create_admin
    monkeypatch.setattr("builtins.input", lambda prompt: "initial-admin")
    monkeypatch.setattr(create_admin, "getpass", lambda prompt: PASSWORD)
    monkeypatch.setattr(create_admin, "get_engine", lambda: session.get_bind())
    assert create_admin.main() == 0
    assert PASSWORD not in capsys.readouterr().out


def test_bootstrap_cli_rejects_mismatched_passwords(session, monkeypatch, capsys):
    from app.scripts import create_admin
    answers = iter([PASSWORD, "different-password"])
    monkeypatch.setattr("builtins.input", lambda prompt: "initial-admin")
    monkeypatch.setattr(create_admin, "getpass", lambda prompt: next(answers))
    assert create_admin.main() == 1
    assert session.exec(select(User)).all() == []
    assert PASSWORD not in capsys.readouterr().out


@pytest.mark.parametrize("path", ["/api/v1/reports/income", "/api/v1/payments/export-csv"])
def test_staff_can_access_protected_reports_and_export(client, make_user, path):
    user = make_user()
    assert client.get(path, headers=headers(user)).status_code == 200
