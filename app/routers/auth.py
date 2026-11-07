from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, select

from app.core.security import (
    blacklist_token, create_access_token, get_current_user, hash_password,
    oauth2_scheme, require_admin, verify_password,
)
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserCreate, UserRead


router = APIRouter(prefix="/auth", tags=["auth"])


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.username == form.username)).first()
    if not user or not user.is_active or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=401, detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(subject=user.id))


@router.post("/register", response_model=UserRead, status_code=201)
def register(
    data: UserCreate,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin),
):
    existing = session.exec(select(User).where(User.username == data.username)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(
        username=data.username,
        hashed_password=hash_password(data.password.get_secret_value()),
        is_admin=data.is_admin,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Username already exists")
    session.refresh(user)
    return user


@router.post("/logout")
def logout(
    user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    blacklist_token(token)
    return {"message": "Successfully logged out"}
