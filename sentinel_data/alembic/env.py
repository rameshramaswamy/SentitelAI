# Alembic Config (to be overwritten by init)
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# --- IMPORT OUR MODELS ---
import sys
import os
sys.path.append(os.getcwd()) # Ensure src is visible
from src.db.models import Base
from src.config import settings

config = context.config

# Overwrite URL from settings (Environment Variable Support)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point to our ORM Metadata
target_metadata = Base.metadata

# ... rest of the file (run_migrations_offline, run_migrations_online) ...