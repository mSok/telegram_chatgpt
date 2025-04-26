import os

import pytest
from playhouse.sqlite_ext import SqliteExtDatabase

from src.database.models import BaseModel, BotAdmin, Chat, ImagePrompt

TEST_DB = "sqlite_db/test.db"

@pytest.fixture(autouse=True)
def test_db():
    """Создаем тестовую базу данных"""
    # Создаем директорию для базы данных, если её нет
    os.makedirs(os.path.dirname(TEST_DB), exist_ok=True)

    # Удаляем тестовую базу, если она существует
    if os.path.exists(TEST_DB):
        os.unlink(TEST_DB)

    # Создаем новую тестовую базу
    test_db = SqliteExtDatabase(
        TEST_DB,
        regexp_function=True,
        timeout=3,
        pragmas={"journal_mode": "wal"}
    )

    # Подменяем базу данных в моделях
    BaseModel._meta.database = test_db

    # Создаем таблицы
    test_db.create_tables([Chat, BotAdmin, ImagePrompt])

    yield test_db

    # Закрываем соединение
    test_db.close()

    # Удаляем тестовую базу
    if os.path.exists(TEST_DB):
        os.unlink(TEST_DB)
