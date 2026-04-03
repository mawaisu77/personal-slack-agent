"""Persist screenshot bytes and return stable URLs for logs and approvals (T-019)."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Protocol, runtime_checkable

from personal_ai.observability.logging import get_logger

log = get_logger(__name__)


@runtime_checkable
class ScreenshotStorage(Protocol):
    def store_png(self, *, task_id: str, name: str, data: bytes) -> str:
        """Return a URL or URI string pointing at the stored object."""


class LocalScreenshotStorage:
    """
    Write PNGs under ``root_dir`` and return ``{public_base_url}/...`` paths.
    Serve ``public_base_url`` from CDN, API static mount, or dev file server separately.
    """

    def __init__(self, root_dir: Path | str, *, public_base_url: str) -> None:
        self._root = Path(root_dir)
        self._root.mkdir(parents=True, exist_ok=True)
        self._public = public_base_url.rstrip("/")

    def store_png(self, *, task_id: str, name: str, data: bytes) -> str:
        safe_task = task_id.replace("/", "_")
        safe_name = name.replace("/", "_") or str(uuid.uuid4())
        if not safe_name.endswith(".png"):
            safe_name += ".png"
        rel = Path(safe_task) / safe_name
        path = self._root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        url_path = str(rel).replace("\\", "/")
        return f"{self._public}/screenshots/{url_path}"


class S3ScreenshotStorage:
    """Upload to S3-compatible storage; returns HTTPS object URL (T-019)."""

    def __init__(
        self,
        *,
        bucket: str,
        key_prefix: str = "screenshots",
        region: str | None = None,
    ) -> None:
        import boto3

        self._bucket = bucket
        self._prefix = key_prefix.strip("/")
        self._client = boto3.client("s3", region_name=region)

    def store_png(self, *, task_id: str, name: str, data: bytes) -> str:
        safe_task = task_id.replace("/", "_")
        safe_name = name.replace("/", "_") or "capture.png"
        if not safe_name.endswith(".png"):
            safe_name += ".png"
        key = f"{self._prefix}/{safe_task}/{safe_name}"
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType="image/png",
        )
        region = self._client.meta.region_name or "us-east-1"
        url = f"https://{self._bucket}.s3.{region}.amazonaws.com/{key}"
        log.info("screenshot_uploaded_s3", bucket=self._bucket, key=key)
        return url
