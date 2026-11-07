"""Create the initial administrator from a trusted operator terminal.

Run after migrations: python -m app.scripts.create_admin
Passwords are prompted without echo and are never accepted as CLI arguments.
"""

from getpass import getpass

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

# Register all tables referenced by the metadata, including relationships.
from app.models.plan import Plan
from app.models.member import Member
from app.models.membership import Membership
from app.models.payment import Payment
from app.models.shift import AvailableShift
from app.models.reservation import Reservation
from app.models.attendance import Attendance
from app.models.user import User
from app.core.security import hash_password
from app.db.session import get_engine
from app.schemas.user import UserCreate


def create_initial_admin(session: Session, data: UserCreate) -> User:
    if session.exec(select(User).where(User.is_admin.is_(True))).first():
        raise ValueError("An administrator already exists; use the authenticated account-creation endpoint")
    if session.exec(select(User).where(User.username == data.username)).first():
        raise ValueError("Username already exists; existing accounts are never promoted or overwritten")
    user = User(
        username=data.username,
        hashed_password=hash_password(data.password.get_secret_value()),
        is_admin=True,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ValueError("Username already exists")
    session.refresh(user)
    return user


def main() -> int:
    username = input("Administrator username: ")
    password = getpass("Password (at least 12 characters, at most 72 UTF-8 bytes): ")
    if password != getpass("Repeat password: "):
        print("Passwords do not match. No account was created.")
        return 1
    try:
        data = UserCreate(username=username, password=password)
    except ValidationError:
        print("Invalid username or password length. No account was created.")
        return 1
    try:
        with Session(get_engine()) as session:
            create_initial_admin(session, data)
    except ValueError as error:
        print(str(error))
        return 1
    print("Initial administrator created. Sign in through /api/v1/auth/token.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
