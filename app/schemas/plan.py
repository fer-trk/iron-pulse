from pydantic import field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlmodel import SQLModel, Field


class PlanBase(SQLModel):
    name: str = Field(max_length=100)
    price: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=8, decimal_places=2)
    description: Optional[str] = Field(default=None, max_length=500)
    duration_days: int = Field(default=30, gt=0)
    active: bool = Field(default=True)


class PlanCreate(PlanBase):
    pass


class PlanUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=100)
    price: Optional[Decimal] = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    description: Optional[str] = None
    duration_days: Optional[int] = Field(default=None, gt=0)
    active: Optional[bool] = None


    @field_validator("name", "price", "duration_days", "active")
    @classmethod
    def reject_null_updates(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class PlanResponse(PlanBase):
    id: int
    created_at: datetime
    updated_at: datetime
