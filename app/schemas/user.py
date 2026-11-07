from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=100)
    password: SecretStr
    is_admin: bool = False

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Username cannot be blank")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        password = value.get_secret_value()
        if len(password) < 12 or len(password.encode("utf-8")) > 72:
            raise ValueError("Password must contain at least 12 characters and at most 72 UTF-8 bytes")
        return value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_admin: bool
    is_active: bool
