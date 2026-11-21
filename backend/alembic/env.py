import os
from app.database import Base
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from dotenv import load_dotenv
from app.database import Base
from app.models import User, Account, Category, Transaction, AuditLog


# Carga las variables definidas en el archivo .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, ".env"))

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL no esta configurada")


# Objeto de configuracion de Alembic
config = context.config

# Usa la URL de PostgreSQL definida en .env
config.set_main_option("sqlalchemy.url", database_url)


# Configuracion de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Modelos que Alembic debe utilizar para detectar cambios
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo offline."""

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
    """Ejecuta migraciones conectandose a la base de datos."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()