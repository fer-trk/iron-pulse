from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import field_validator
from ..models.payment import PaymentMethod, PaymentStatus


class PaymentBase(SQLModel):
    membership_id: int
    amount: Optional[Decimal] = Field(default=None, gt=0, max_digits=8, decimal_places=2)
    payment_method: PaymentMethod
    status: PaymentStatus = PaymentStatus.pending
    reference: str = ""
    notes: str = ""

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("The amount must be greater than 0")
        return v


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(SQLModel):
    status: Optional[PaymentStatus] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


    @field_validator("status", "reference", "notes")
    @classmethod
    def reject_explicit_null(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class PaymentRead(PaymentBase):
    id: int
    payment_date: datetime
    created_at: datetime
