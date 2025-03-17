import logging
import random
import telegram
from telegram.ext import CallbackContext
from telegram import Update

from src import config
from src.database import models
from src.open_ai import chat_gpt
from ..utils import check_access_to_chat
from .image import generate_image

log = logging.getLogger(__name__)

async def request(update: Update, context: CallbackContext):
    """Обработка команды /request"""
    log.debug("request %s", update.message.text if update.message else "No message")

    if not check_access_to_chat(update):
        return

    message = update.message
    if not message or not message.text:
        log.error("Update message or text is None")
        return

    chat = models.Chat.get_by_id(message.chat_id)
    if not chat:
        log.error("Chat not found")
        return

    # Получаем текст запроса
    request_text = message.text.removeprefix("/request")

    # Получаем ответ от GPT
    answer = chat_gpt.get_answer(
        prompt=chat.prompt,
        message=request_text,
        conversation_id=chat.id,
    )

    # Разбиваем ответ на части, если он слишком длинный
    max_length = 4096
    parts = [answer[i:i + max_length] for i in range(0, len(answer), max_length)]
    for part in parts:
        await message.reply_text(text=part)

    # % шанс сгенерировать изображение
    if random.random() < chat.img_chance:
        await generate_image(update=update, context=context)

async def on_message(update: Update, context: CallbackContext):
    """Обработка обычных сообщений"""
    message = update.message
    if not message or not message.text:
        log.error("Update message or text is None")
        return

    log.debug("on_message %s", message.text)

    if not check_access_to_chat(update):
        return

    chat = models.Chat.get_by_id(message.chat_id)
    if not chat:
        log.error("Chat not found")
        return

    if chat.mode != "member":
        return

    # Получаем ответ от GPT
    answer = chat_gpt.get_answer(
        prompt=chat.prompt,
        message=message.text,
        conversation_id=chat.id,
    )

    # Отправляем ответ
    await context.bot.send_message(
        chat_id=message.chat_id,
        text=answer,
    )

    # % шанс сгенерировать изображение
    if random.random() < chat.img_chance:
        await generate_image(update=update, context=context)