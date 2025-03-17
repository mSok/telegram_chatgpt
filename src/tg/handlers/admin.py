import json
import logging
from typing import Optional
import telegram
from telegram.ext import CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update

from src import config
from src.constants import BotMode
from src.database import models
from src.open_ai import chat_gpt
from ..utils import check_access_to_chat

log = logging.getLogger(__name__)

def get_message_and_chat_id(update: Update) -> tuple[Optional[Message], Optional[int]]:
    """Helper function to get message and chat_id with proper type checking"""
    message = update.message if update and update.message else None
    chat_id = message.chat_id if message and message.chat else None
    return message, chat_id

async def set_enable(update: Update, context: CallbackContext):
    """Активируем бота в чате"""
    log.debug("enable command")

    if not check_access_to_chat(update, check_admin_rights=True):
        return

    message, chat_id = get_message_and_chat_id(update)
    if not chat_id:
        log.error("Chat ID is None")
        return

    models.Chat.set_state(chat_id, True)
    chat = models.Chat.get_by_id(chat_id)
    if not chat:
        log.error("Chat not found")
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=config.DEFAULT_BOT_PROMPT + f"""prompt: {chat.prompt}""",
    )

async def set_disable(update: Update, context: CallbackContext):
    """Деактивируем бота в чате"""
    log.debug("disable command")
    if not check_access_to_chat(update):
        return

    message, chat_id = get_message_and_chat_id(update)
    if not chat_id:
        log.error("Chat ID is None")
        return

    models.Chat.set_state(chat_id, False)
    await context.bot.send_message(
        chat_id=chat_id,
        text="Я отключился. Всем пока в этом чате."
    )

async def set_prompt(update: Update, context: CallbackContext):
    """Установит контекст для бота в чате"""
    log.debug("set_prompt command")
    if not check_access_to_chat(update):
        return

    message, chat_id = get_message_and_chat_id(update)
    if not message or not chat_id:
        log.error("Message or chat_id is None")
        return

    prompt_text = message.text
    if not prompt_text:
        log.error("Message text is None")
        return

    new_prompt = models.Chat.set_prompt(chat_id, prompt_text.removeprefix("/set_prompt"))
    chat_gpt.clear_conversation(chat_id)

    return await context.bot.send_message(
        chat_id=chat_id,
        text=f"У меня установлен следующий prompt: \n```{new_prompt}```",
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
    )

async def set_default_prompt(update: Update, context: CallbackContext):
    """Сбросить на дефолтный контекст."""
    log.debug("set_default_prompt command")
    if not check_access_to_chat(update):
        return

    message, chat_id = get_message_and_chat_id(update)
    if not chat_id:
        log.error("Chat ID is None")
        return

    new_prompt = models.Chat.set_prompt(chat_id, config.DEFAULT_PROMPT)
    chat_gpt.clear_conversation(chat_id)

    return await context.bot.send_message(
        chat_id=chat_id,
        text=f"У меня установлен следующий prompt: \n```{new_prompt}```",
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
    )

async def clear(update: Update, context: CallbackContext):
    """Очистить историю/контекст бота"""
    log.debug("clear command")
    if not check_access_to_chat(update):
        return

    message, chat_id = get_message_and_chat_id(update)
    if not chat_id:
        log.error("Chat ID is None")
        return

    chat_gpt.clear_conversation(chat_id)
    return await context.bot.send_message(
        chat_id=chat_id,
        text="Ok."
    )

async def set_mode(update: Update, context: CallbackContext):
    """Установить способ участия бота в чате.
        member: Отвечает на все
        request: только на команду /request
    """
    log.debug("set_mode command")
    if not check_access_to_chat(update):
        return

    message, chat_id = get_message_and_chat_id(update)
    if not message or not chat_id:
        log.error("Message or chat_id is None")
        return

    mode_text = message.text
    if not mode_text:
        log.error("Message text is None")
        return

    mode = mode_text.removeprefix("/set_mode").strip()
    log.debug("set_mode command %s message for %s", mode, chat_id)

    if not mode in BotMode.__members__:
        return await context.bot.send_message(
            chat_id=chat_id,
            text="Only `member` or `request`",
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
        )

    chat = models.Chat.get_by_id(chat_id)
    if not chat:
        log.error("Chat not found")
        return

    new_mode = models.Chat.set_mode(chat_id, BotMode(mode))
    return await context.bot.send_message(
        chat_id=chat_id,
        text=f"Ok. {new_mode}",
    )

async def get_status(update: Update, context: CallbackContext):
    """Вернет текущие настройки бота"""
    log.debug("get_status command")

    message, chat_id = get_message_and_chat_id(update)
    if not chat_id:
        log.error("Chat ID is None")
        return

    chat = models.Chat.get_by_id(chat_id)
    if not chat:
        log.error("Chat not found")
        return

    json_data = json.dumps(
        {
            "enable": chat.enable,
            "mode": chat.mode,
            "prompt": chat.prompt,
            "model": config.AI_MODEL,
            "chat_id": chat_id,
        },
        indent=4,
        default=str,
        ensure_ascii=False,
    )

    return await context.bot.send_message(
        chat_id=chat_id,
        text=f"""<code>{json_data}</code>""",
        parse_mode=telegram.constants.ParseMode.HTML,
    )

async def request_admin_approval(bot, chat_id: int, admin_id: int):
    """Запрос на добавление бота в чат"""
    try:
        chat = await bot.get_chat(chat_id)
        chat_title = chat.title if chat else 'неизвестный чат'
        log.info("Имя чата: %s", chat_title)
    except Exception as e:
        log.error("Ошибка при получении информации о чате: %s", e)
        return

    # Создаем кнопки для подтверждения или отклонения
    keyboard = [
        [
            InlineKeyboardButton("Разрешить", callback_data=f"approve_{chat_id}"),
            InlineKeyboardButton("Отклонить", callback_data=f"deny_{chat_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Создаем ссылку на чат
    chat_link = f"https://t.me/c/{chat_id}"

    # Отправляем сообщение админу
    await bot.send_message(
        chat_id=admin_id,
        text=f"Вы хотите разрешить боту отвечать в чате <a href='{chat_link}'>{chat_title}</a> (ID: {chat_id})?",
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.HTML
    )
    return True

async def add_chat_or_user(update: Update, context: CallbackContext):
    """Добавить чат или пользователя в белый список"""
    log.debug("add_chat_or_user command")
    if not check_access_to_chat(update, check_admin_rights=True):
        return

    message, chat_id = get_message_and_chat_id(update)
    if not chat_id:
        log.error("Chat ID is None")
        return

    # Отправляем запрос админу на добавление чата или пользователя
    await request_admin_approval(context.bot, chat_id, config.TELEGRAM_ADMIN_USER_ID)