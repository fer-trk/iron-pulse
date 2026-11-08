from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Numeric
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .membership import Membership


class Plan(SQLModel, table=True):
    __tablename__ = "plans"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    price: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(8, 2), nullable=False))
    description: Optional[str] = Field(default=None, max_length=500)
    duration_days: int = Field(default=30, gt=0)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    memberships: List["Membership"] = Relationship(back_populates="plan")
