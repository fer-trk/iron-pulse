from pydantic import field_validator
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class MemberBase(SQLModel):
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    email: str = Field(max_length=150)
    phone: Optional[str] = Field(default=None, max_length=20)
    is_active: bool = Field(default=True)


class MemberCreate(MemberBase):
    pass


class MemberUpdate(SQLModel):
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=150)
    phone: Optional[str] = None
    is_active: Optional[bool] = None


    @field_validator("first_name", "last_name", "email", "is_active")
    @classmethod
    def reject_null_updates(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class MemberRead(MemberBase):
    id: int
    registration_date: datetime