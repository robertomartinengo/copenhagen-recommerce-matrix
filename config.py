"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Optional PostHog configuration for the FastAPI application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_environment: str = "development"
    posthog_project_token: str | None = None
    posthog_host: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
