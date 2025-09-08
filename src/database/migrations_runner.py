import importlib
import os
from datetime import datetime

import peewee

from src.database.models import BaseModel, sql_lite_db


class MigrationRecord(BaseModel):
    name = peewee.CharField(unique=True)
    applied_at = peewee.DateTimeField(default=datetime.now)


def _ensure_migrations_table():
    sql_lite_db.create_tables([MigrationRecord], safe=True)


def _list_migration_modules() -> list[str]:
    base_dir = os.path.join(os.path.dirname(__file__), "migrations")
    if not os.path.isdir(base_dir):
        return []
    files = [f for f in os.listdir(base_dir) if f.endswith('.py') and f[:4].isdigit()]
    files.sort()
    return [f"src.database.migrations.{os.path.splitext(f)[0]}" for f in files]



def run_migrations() -> None:
    _ensure_migrations_table()

    applied = {m.name for m in MigrationRecord.select()}
    for module_name in _list_migration_modules():
        if module_name in applied:
            continue

        module = importlib.import_module(module_name)
        migrate_fn = getattr(module, "apply", None) or getattr(module, "up", None)
        if not migrate_fn:
            # пропускаем файл без экспортированной функции миграции
            continue

        migrate_fn(sql_lite_db)
        MigrationRecord.create(name=module_name)


