from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from app.core.config import settings
from app.core.database import Base
from app.models import (
    User,
    Product,
    Cart,
    Order,
    OrderItem,
    Payment,
    WebhookEvent,
    ReturnRequest,
)

from alembic import context


# =========================================================
# Alembic Config
# =========================================================

config = context.config


# =========================================================
# Logging
# =========================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# =========================================================
# SQLAlchemy Metadata
# =========================================================

target_metadata = Base.metadata


# =========================================================
# Ignore Django-managed tables
# =========================================================

DJANGO_TABLES = {
    "django_migrations",
    "django_session",
    "django_admin_log",
    "django_content_type",
    "auth_permission",
    "auth_group",
    "auth_group_permissions",
    "auth_user",
    "auth_user_groups",
    "auth_user_user_permissions",
}


def include_object(
    object,
    name,
    type_,
    reflected,
    compare_to,
):
    """
    Tell Alembic which database objects should be
    included during autogeneration.

    Django owns its own tables, so Alembic must ignore them.
    """

    if type_ == "table" and name in DJANGO_TABLES:
        return False

    return True


# =========================================================
# Offline Migration
# =========================================================

def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================================================
# Online Migration
# =========================================================

def run_migrations_online() -> None:

    configuration = config.get_section(
        config.config_ini_section,
        {},
    )

    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


# =========================================================
# Run
# =========================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()