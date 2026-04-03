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

    worker_max_job_retries: int = Field(default=3, ge=1, alias="WORKER_MAX_JOB_RETRIES")

    # Web agent: "stub" keeps fast no-browser path for tests; "loop" runs Playwright + T-023.
    agent_web_mode: Literal["stub", "loop"] = Field(default="stub", alias="AGENT_WEB_MODE")
    agent_max_steps: int = Field(default=40, ge=1, le=500, alias="AGENT_MAX_STEPS")
    agent_max_duration_seconds: float = Field(
        default=300.0,
        ge=5.0,
        alias="AGENT_MAX_DURATION_SECONDS",
    )
    agent_max_ai_calls: int = Field(default=50, ge=1, alias="AGENT_MAX_AI_CALLS")
    agent_no_op_streak_limit: int = Field(default=2, ge=1, le=20, alias="AGENT_NO_OP_STREAK_LIMIT")
    agent_checkpoint_every_n_steps: int = Field(
        default=1,
        ge=0,
        le=100,
        alias="AGENT_CHECKPOINT_EVERY_N_STEPS",
        description="0 disables T-055 checkpoint writes during the loop.",
    )

    approval_poll_interval_sec: float = Field(
        default=2.0,
        ge=0.5,
        alias="APPROVAL_POLL_INTERVAL_SEC",
    )
    approval_wait_timeout_sec: float = Field(
        default=3600.0,
        ge=30.0,
        alias="APPROVAL_WAIT_TIMEOUT_SEC",
    )
    # T-040: JSON policy (see config/approval_policy.example.json).
    approval_policy_path: str | None = Field(default=None, alias="APPROVAL_POLICY_PATH")

    # T-054 / T-057: 0 = unlimited.
    max_concurrent_tasks_per_user: int = Field(
        default=0,
        ge=0,
        alias="MAX_CONCURRENT_TASKS_PER_USER",
    )
    max_daily_tasks_per_user: int = Field(
        default=0,
        ge=0,
        alias="MAX_DAILY_TASKS_PER_USER",
    )

    screenshot_storage_dir: str = Field(default="var/screenshots", alias="SCREENSHOT_STORAGE_DIR")
    public_assets_base_url: str = Field(
        default="http://localhost:8080",
        alias="PUBLIC_ASSETS_BASE_URL",
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
