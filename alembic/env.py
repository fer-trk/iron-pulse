from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

from app.core.config import settings
# Register every table for Alembic autogeneration.
from app.models.plan import Plan  # noqa: F401
from app.models.member import Member  # noqa: F401
from app.models.membership import Membership  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.shift import AvailableShift  # noqa: F401
from app.models.reservation import Reservation  # noqa: F401
from app.models.user import User  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata
# Share the application's URL precedence and .env support. Pass the URL directly
# instead of through ConfigParser, which interprets percent-encoded credentials.
database_url = settings.get_database_url()


def run_migrations_offline():
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(database_url, poolclass=pool.NullPool)
    try:
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
