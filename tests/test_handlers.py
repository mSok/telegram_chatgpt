from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import ContextTypes

from src.constants import BotMode
from src.database.models import BotAdmin
from src.tg.handlers.admin import set_disable, set_enable, set_mode


@pytest.fixture
def mock_update() -> MagicMock:
    """Фикстура для создания мока Update"""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.chat = MagicMock(spec=Chat)
    update.message.chat_id = 123456789  # Добавляем chat_id напрямую в message
    update.message.from_user = MagicMock(spec=User)
    update.message.from_user.id = 987654321
    update.message.from_user.username = "test_user"
    return update

@pytest.fixture
def mock_context() -> MagicMock:
    """Фикстура для создания мока Context"""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    return context

@pytest.fixture(autouse=True)
def setup_admin() -> Generator[None, None, None]:
    """Создаем тестового админа"""
    BotAdmin.create(id=987654321, name="test_admin")
    yield
    BotAdmin.delete().execute()

@pytest.mark.asyncio
async def test_set_enable_command(mock_update: MagicMock, mock_context: MagicMock) -> None:
    """Тест команды /enable"""
    with patch('src.tg.utils.check_access_to_chat', return_value=True):
        await set_enable(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        args = mock_context.bot.send_message.call_args
        assert args[1]['chat_id'] == 123456789

@pytest.mark.asyncio
async def test_set_disable_command(mock_update: MagicMock, mock_context: MagicMock) -> None:
    """Тест команды /disable"""
    with patch('src.tg.utils.check_access_to_chat', return_value=True):
        await set_disable(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        args = mock_context.bot.send_message.call_args
        assert args[1]['chat_id'] == 123456789
        assert "отключился" in args[1]['text']

@pytest.mark.asyncio
async def test_set_mode_command(mock_update: MagicMock, mock_context: MagicMock) -> None:
    """Тест команды /mode"""
    mock_update.message.text = f"/set_mode {BotMode.member.value}"

    with patch('src.tg.utils.check_access_to_chat', return_value=True):
        await set_mode(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once()
        args = mock_context.bot.send_message.call_args
        assert args[1]['chat_id'] == 123456789
        assert "Ok" in args[1]['text']
