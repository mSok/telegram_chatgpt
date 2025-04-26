from collections.abc import Generator

import pytest

from src.constants import BotMode
from src.database.models import Chat


@pytest.fixture(autouse=True)
def cleanup_database() -> Generator[None, None, None]:
    """Очищаем базу данных перед каждым тестом"""
    Chat.delete().execute()
    yield
    Chat.delete().execute()

@pytest.mark.asyncio
async def test_create_chat() -> None:
    """Тест создания чата"""
    chat_id = 123456789
    chat = Chat.create(
        id=chat_id,
        enable=True,
        mode=BotMode.member.value
    )

    assert chat.id == chat_id
    assert chat.enable is True
    assert chat.mode == BotMode.member.value

@pytest.mark.asyncio
async def test_set_chat_state() -> None:
    """Тест изменения состояния чата"""
    chat_id = 987654321
    state = True

    result = Chat.set_state(chat_id, state)

    assert result is True
    chat = Chat.get(Chat.id == chat_id)
    assert chat.enable is True

@pytest.mark.asyncio
async def test_set_chat_mode() -> None:
    """Тест изменения режима чата"""
    chat_id = 11111111
    mode = BotMode.member

    result = Chat.set_mode(chat_id, mode)

    assert result == mode.value
    chat = Chat.get(Chat.id == chat_id)
    assert chat.mode == mode.value
