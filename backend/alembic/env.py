"""
Alembic environment — configured for Sentinel sync PostgreSQL.
Reads DATABASE_URL from environment (never hardcoded).
"""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add backend directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env for local development
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Import all models so their metadata is available
import app.models  # noqa: F401
from app.core.database import Base

# Alembic config object
config = context.config

# Override sqlalchemy.url from environment (NEVER from alembic.ini)
database_url = os.environ.get("DATABASE_URL", "")
if not database_url:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        "Check your .env file."
    )

# Alembic runs synchronously — convert asyncpg to psycopg2
sync_url = database_url.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
)
config.set_main_option("sqlalchemy.url", sync_url)

# Logging configuration
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL scripts)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (against live database)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
