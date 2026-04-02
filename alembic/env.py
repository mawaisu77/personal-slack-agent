from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text

from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from personal_ai.config.settings import get_settings
from personal_ai.db.base import Base
from personal_ai.observability.logging import configure_logging, get_logger
from personal_ai.state import models as _state_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

configure_logging(json_logs=os.environ.get("LOG_FORMAT", "").lower() == "json")
log = get_logger(__name__)

target_metadata = Base.metadata


def get_url() -> str:
    return get_settings().database_url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        try:
            row = connection.execute(text("SELECT version_num FROM alembic_version")).fetchone()
            version = row[0] if row else "unknown"
        except Exception:
            version = "unknown"
        log.info("migration_complete", revision_applied=version)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
