import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from sqlalchemy import event
from decimal import Decimal
from datetime import date, timedelta

import app.models  # ensure all models are registered with SQLAlchemy before create_all
from main import app as fastapi_app
from app.db.session import get_session
from app.models.membership import Membership, MembershipStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus


# ── Fixtures de infraestructura ────────────────────────────────────────────
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    SQLModel.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def override():
        yield session
    previous = fastapi_app.dependency_overrides.copy()
    fastapi_app.dependency_overrides[get_session] = override
    try:
        with TestClient(fastapi_app) as client:
            yield client
    finally:
        fastapi_app.dependency_overrides.clear()
        fastapi_app.dependency_overrides.update(previous)


# ── Auth (stub sin JWT real) ───────────────────────────────────────────────
@pytest.fixture(name="auth_headers")
def auth_headers_fixture():
    from app.core.security import get_current_user_sub
    previous = fastapi_app.dependency_overrides.get(get_current_user_sub)
    fastapi_app.dependency_overrides[get_current_user_sub] = lambda: 1
    try:
        yield {}
    finally:
        if previous is None:
            fastapi_app.dependency_overrides.pop(get_current_user_sub, None)
        else:
            fastapi_app.dependency_overrides[get_current_user_sub] = previous


# ── Datos de prueba ────────────────────────────────────────────────────────
@pytest.fixture(name="monthly_plan")
def monthly_plan_fixture(session: Session):
    from app.models.plan import Plan
    plan = Plan(name="Monthly", price=Decimal("49.99"), duration_days=30, active=True)
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


@pytest.fixture(name="active_member")
def active_member_fixture(session: Session):
    from app.models.member import Member, MemberStatus
    m = Member(first_name="Carlos", last_name="García", email="carlos@gym.es",
               phone="+34600000001", status=MemberStatus.active)
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


@pytest.fixture(name="active_membership")
def active_membership_fixture(session: Session, active_member, monthly_plan):
    today = date.today()
    m = Membership(
        member_id=active_member.id, plan_id=monthly_plan.id,
        start_date=today, end_date=today + timedelta(days=30),
        status=MembershipStatus.active,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m
