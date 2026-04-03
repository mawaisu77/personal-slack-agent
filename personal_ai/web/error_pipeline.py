"""Screenshot + user notification on web automation failures (T-027)."""

from __future__ import annotations

from typing import Any

from personal_ai.config.settings import get_settings
from personal_ai.observability.logging import get_logger
from personal_ai.queue.schemas import JobPayload
from personal_ai.slack_interface.progress import post_task_terminal_note
from personal_ai.web.screenshot_storage import LocalScreenshotStorage

log = get_logger(__name__)


def notify_web_task_error(
    job: JobPayload,
    exc: BaseException,
    *,
    page: Any | None = None,
) -> None:
    """Best-effort screenshot URL + Slack ephemeral when payload has a channel (T-027)."""
    raw_ch = job.payload.get("slack_channel_id") if isinstance(job.payload, dict) else None
    channel_id = raw_ch.strip() if isinstance(raw_ch, str) else None
    if not channel_id:
        log.info("web_error_no_slack_channel", task_id=str(job.task_id))
        return

    parts = [f"Error: {exc!s}"]
    screenshot_url: str | None = None
    if page is not None:
        try:
            png = page.screenshot(type="png", full_page=True)
            settings = get_settings()
            store = LocalScreenshotStorage(
                settings.screenshot_storage_dir,
                public_base_url=settings.public_assets_base_url,
            )
            screenshot_url = store.store_png(
                task_id=str(job.task_id),
                name="error",
                data=bytes(png),
            )
            parts.append(f"screenshot: {screenshot_url}")
        except Exception as cap_exc:  # noqa: BLE001
            log.warning("web_error_screenshot_failed", error=str(cap_exc))
        try:
            url = getattr(page, "url", None)
            if url:
                parts.append(f"url: {url}")
        except Exception:  # noqa: BLE001
            pass

    summary = "\n".join(parts)[:1500]
    try:
        post_task_terminal_note(
            user_id=job.user_id,
            channel_id=channel_id,
            task_id=job.task_id,
            summary=summary,
        )
    except Exception as post_exc:  # noqa: BLE001
        log.warning("web_error_slack_failed", error=str(post_exc))
