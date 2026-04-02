from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment; sensitive values via get_secret()."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["dev", "staging", "prod"] = "dev"

    # Secrets: "env" = read from process environment; "aws" = JSON bundle in AWS Secrets Manager
    secrets_mode: Literal["env", "aws"] = Field(
        default="env",
        description="env: plaintext only in local .env; aws: load from Secrets Manager (prod).",
    )
    aws_region: str | None = None
    # Single secret in AWS containing JSON object of key -> value (e.g. {"SLACK_BOT_TOKEN": "..."})
    aws_app_secret_id: str | None = Field(
        default=None,
        description="Secrets Manager SecretId (name or ARN) for the JSON bundle of app secrets.",
    )

    # Database URL for sync operations (Alembic, migration scripts). Use psycopg3 driver.
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/personal_ai",
        alias="DATABASE_URL",
    )

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Playwright persistent profile (T-017); one dir per deployment/process.
    playwright_user_data_dir: str = Field(
        default=".playwright-profile",
        alias="PLAYWRIGHT_USER_DATA_DIR",
    )

    # vapi | bland | retell | noop (T-028)
    voice_provider: Literal["noop", "vapi", "bland", "retell"] = Field(
        default="noop",
        alias="VOICE_PROVIDER",
    )

    @model_validator(mode="after")
    def _validate_aws_for_prod(self) -> "Settings":
        if self.secrets_mode == "aws" and not self.aws_app_secret_id:
            msg = "aws_app_secret_id is required when secrets_mode=aws"
            raise ValueError(msg)
        if self.secrets_mode == "aws" and not self.aws_region:
            msg = "aws_region is required when secrets_mode=aws"
            raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Clear settings cache (tests)."""
    get_settings.cache_clear()
