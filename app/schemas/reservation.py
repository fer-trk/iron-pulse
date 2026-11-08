from datetime import date, datetime
from pydantic import field_validator
from sqlmodel import SQLModel, Field


class ReservationCreate(SQLModel):
    member_id: int = Field(gt=0)
    shift_id: int = Field(gt=0)
    date: date

    @field_validator("date")
    @classmethod
    def not_in_past(cls, value):
        if value < date.today():
            raise ValueError("Enrollment date cannot be in the past")
        return value


class ReservationRead(SQLModel):
    id: int
    member_id: int
    shift_id: int
    date: date
    status: str
    created_at: datetime
    updated_at: datetime
