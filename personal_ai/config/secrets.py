from __future__ import annotations

import json
import os
from typing import Any

from personal_ai.config.settings import get_settings


class MissingSecretError(RuntimeError):
    """Raised when a required secret is not present in the configured backend."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Required secret missing: {name}")
        self.name = name


_aws_bundle_cache: dict[str, str] | None = None


def clear_secret_cache() -> None:
    """Clear cached AWS secret bundle (tests or rotation)."""
    global _aws_bundle_cache
    _aws_bundle_cache = None


def _load_aws_bundle() -> dict[str, str]:
    global _aws_bundle_cache
    if _aws_bundle_cache is not None:
        return _aws_bundle_cache

    import boto3

    settings = get_settings()
    if not settings.aws_app_secret_id or not settings.aws_region:
        raise MissingSecretError("AWS_SECRET_CONFIG")

    client = boto3.client("secretsmanager", region_name=settings.aws_region)
    resp = client.get_secret_value(SecretId=settings.aws_app_secret_id)
    raw = resp.get("SecretString")
    if raw is None:
        raise MissingSecretError(settings.aws_app_secret_id)

    data: Any = json.loads(raw)
    if not isinstance(data, dict):
        msg = "AWS app secret must be a JSON object of string keys to string values"
        raise ValueError(msg)

    out: dict[str, str] = {}
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            msg = "AWS app secret JSON must map string keys to string values"
            raise ValueError(msg)
        out[k] = v

    _aws_bundle_cache = out
    return out


def get_secret(name: str) -> str:
    """
    Load a secret by logical name (e.g. SLACK_BOT_TOKEN).

    - secrets_mode=env: read os.environ[name] (use .env locally; never commit real values).
    - secrets_mode=aws: read from the JSON bundle stored in aws_app_secret_id.
    """
    settings = get_settings()
    if settings.secrets_mode == "env":
        value = os.environ.get(name)
        if value is None or value == "":
            raise MissingSecretError(name)
        return value

    bundle = _load_aws_bundle()
    if name not in bundle:
        raise MissingSecretError(name)
    return bundle[name]


def require_secrets(*names: str) -> None:
    """Fail fast at startup if any named secret is missing."""
    for name in names:
        get_secret(name)
