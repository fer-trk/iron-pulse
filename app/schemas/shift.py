from pydantic import field_validator
from datetime import time, datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field
from app.models.shift import DayOfWeek


class ShiftBase(SQLModel):
    class_name: str = Field(max_length=100)
    instructor: str = Field(max_length=100)
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    max_capacity: int = Field(gt=0)
    active_slot: bool = Field(default=True)


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(SQLModel):
    class_name: Optional[str] = Field(default=None, max_length=100)  # fixed
    instructor: Optional[str] = Field(default=None, max_length=100)
    day_of_week: Optional[DayOfWeek] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    max_capacity: Optional[int] = Field(default=None, gt=0)
    active_slot: Optional[bool] = None


    @field_validator("class_name", "instructor", "day_of_week", "start_time", "end_time", "max_capacity", "active_slot")
    @classmethod
    def reject_null_updates(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class ShiftRead(ShiftBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ShiftAvailability(SQLModel):
    shift_id: int
    shift_name: str
    date: date
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    max_capacity: int
    active_bookings: int
    available_spots: int
    is_available: bool