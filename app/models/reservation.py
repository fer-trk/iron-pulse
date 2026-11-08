from datetime import datetime, date
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint

if TYPE_CHECKING:
    from .shift import AvailableShift
    from .member import Member


class ReservationStatus(str, Enum):
    confirmed = "confirmed"
    cancelled = "cancelled"
    no_show = "no_show"


class Reservation(SQLModel, table=True):
    __tablename__ = "reservations"
    __table_args__ = (
        UniqueConstraint("member_id", "shift_id", "date", name="uq_reservation_member_shift_date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    member_id: Optional[int] = Field(default=None, foreign_key="members.id")
    shift_id: Optional[int] = Field(default=None, foreign_key="available_shifts.id")
    date: date
    status: ReservationStatus = Field(default=ReservationStatus.confirmed)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    member: Optional["Member"] = Relationship(back_populates="reservations")
    shift: Optional["AvailableShift"] = Relationship(back_populates="reservations")
