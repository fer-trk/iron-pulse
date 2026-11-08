from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Numeric
from enum import Enum

if TYPE_CHECKING:
    from .member import Member
    from .plan import Plan
    from .payment import Payment


class MembershipStatus(str, Enum):
    pending = "pending"
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class Membership(SQLModel, table=True):
    """Contract between a Member and a Plan with a validity period."""
    __tablename__ = "memberships"

    id: Optional[int] = Field(default=None, primary_key=True)
    member_id: int = Field(foreign_key="members.id", index=True)
    plan_id: int = Field(foreign_key="plans.id", index=True)
    start_date: date
    end_date: Optional[date] = Field(default=None)
    status: MembershipStatus = Field(default=MembershipStatus.pending)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    member: Optional["Member"] = Relationship(back_populates="memberships")
    plan: Optional["Plan"] = Relationship(back_populates="memberships")
    payments: List["Payment"] = Relationship(back_populates="membership")

    def calculate_end_date(self, duration_days: int) -> None:
        """Call after the plan duration is known."""
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=duration_days)

    @property
    def is_active(self) -> bool:
        today = date.today()
        return (
            self.status == MembershipStatus.active
            and self.end_date is not None
            and self.start_date <= today <= self.end_date
        )

    @property
    def days_remaining(self) -> int:
        if not self.end_date:
            return 0
        return (self.end_date - date.today()).days
