from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session

from app.core.config import settings
from app.db.session import get_session
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Process-local until the separate persistent-session improvement is implemented.
token_blacklist: set[str] = set()


def blacklist_token(token: str) -> None:
    token_blacklist.add(token)


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(password) < 12 or len(encoded) > 72:
        raise ValueError("Password must contain at least 12 characters and at most 72 UTF-8 bytes")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except (ValueError, UnicodeError):
        # Malformed hashes and overlong passwords are invalid credentials.
        return False


def create_access_token(subject: int, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return jwt.encode(
        {"sub": str(subject), "exp": expire, "type": "access", "jti": str(uuid4())},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )


def invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    if token in token_blacklist:
        raise invalid_credentials()
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
            options={"require_exp": True, "require_sub": True},
        )
        subject = payload["sub"]
        if payload.get("type") != "access" or not subject.isascii() or not subject.isdecimal():
            raise invalid_credentials()
        user_id = int(subject)
        if user_id <= 0 or user_id > 2147483647:
            raise invalid_credentials()
    except (JWTError, ValueError, TypeError, AttributeError):
        raise invalid_credentials()

    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise invalid_credentials()
    return user


def get_current_user_sub(user: User = Depends(get_current_user)) -> int:
    return user.id


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Administrator permissions required")
    return user
