from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from enum import Enum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.reservation import Reservation
    from app.models.membership import Membership


class MemberStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"

class Member(SQLModel, table=True):
    __tablename__ = "members"

    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    email: str = Field(unique=True, index=True, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=20)
    registration_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = Field(default=True)
    status: MemberStatus = Field(default=MemberStatus.active)

    reservations: List["Reservation"] = Relationship(back_populates="member")
    memberships: List["Membership"] = Relationship(back_populates="member")
