from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CI Failure Doctor"
    app_env: str = "development"
    debug: bool = True

    github_webhook_secret: str = ""

    database_url: str = (
        "postgresql+psycopg://ci_doctor:ci_doctor_dev@localhost:5432/ci_doctor"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()