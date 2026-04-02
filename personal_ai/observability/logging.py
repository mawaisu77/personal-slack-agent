from __future__ import annotations

import logging
import sys

import structlog

from personal_ai.observability.context import context_dict


def _merge_task_context(
    logger: logging.Logger, method_name: str, event_dict: structlog.types.EventDict
) -> structlog.types.EventDict:
    event_dict.update(context_dict())
    return event_dict


def configure_logging(*, json_logs: bool = False, level: int = logging.INFO) -> None:
    """Configure structlog once; JSON for production grep, console for local dev."""
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        _merge_task_context,
        structlog.processors.add_log_level,
        timestamper,
    ]
    if json_logs:
        processors.extend(
            [
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ]
        )
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name)
