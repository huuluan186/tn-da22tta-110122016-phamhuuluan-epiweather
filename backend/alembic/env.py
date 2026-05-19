import re
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.core.config import settings  # noqa: E402
import app.db.base  # noqa: E402, F401 — register all models vào Base.metadata
from app.db.base_class import Base  # noqa: E402

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata

# Partition tables (ví dụ: disease_cases_2010, weather_obs_default, api_logs_2026)
# được quản lý bởi PostgreSQL partitioning, không phải SQLAlchemy ORM.
# Alembic không được touch các bảng này.
_PARTITION_PATTERN = re.compile(
    r"^(disease_cases|weather_obs|weather_observations|predictions|api_logs|api_request_logs)_(\d{4}|default)$"
)


def include_object(obj, name, type_, reflected, compare_to):
    """Trả False cho các partition tables để Alembic bỏ qua hoàn toàn."""
    if type_ == "table" and _PARTITION_PATTERN.match(name):
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
