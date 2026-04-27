"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    DATABASE_URL: str = "postgresql+asyncpg://trackedux_user:admin@localhost:5432/trackedux"
    JWT_SECRET: str = "change_me_to_a_random_secret_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_TTL_MINUTES: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 7
    DEFAULT_LANGUAGE: str = "vi"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
