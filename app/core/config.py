from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
from sqlalchemy.engine import URL


DEVELOPMENT_SECRET = "dev-insecure-key-cambiar-en-produccion-minimo-32"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", hide_input_in_errors=True)
    APP_NAME: str = "GymAPI"
    DEBUG: bool = True
    SECRET_KEY: str = DEVELOPMENT_SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, gt=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0)

    DB_NAME: str = "gym_db"
    DB_USER: str = "gymuser"
    DB_PASSWORD: str = "gympassword"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    DATABASE_URL: Optional[str] = None

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return URL.create(
            "postgresql", username=self.DB_USER, password=self.DB_PASSWORD,
            host=self.DB_HOST, port=self.DB_PORT, database=self.DB_NAME,
            query={"sslmode": "disable"},
        ).render_as_string(hide_password=False)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @model_validator(mode="after")
    def validate_production_secret(self):
        if not self.DEBUG and (
            len(self.SECRET_KEY.strip()) < 32
            or self.SECRET_KEY in {DEVELOPMENT_SECRET, "your-secret-key-min-32-chars-here"}
        ):
            raise ValueError("Production requires a private SECRET_KEY of at least 32 characters")
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
