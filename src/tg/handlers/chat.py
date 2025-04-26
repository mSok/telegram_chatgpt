import logging

import telegram
from telegram.ext import CallbackContext

from src.database import models
from src.open_ai import chat_gpt

from ..utils import check_access_to_chat

log = logging.getLogger(__name__)

async def request(update: telegram.Update, context: CallbackContext):
    log.debug("request %s", update.message.text if update.message else "No message")

    if not check_access_to_chat(update):
        return

    if not update.message or not update.message.text:
        log.error("Update message or text is None")
        return

    message = update.message.text.removeprefix("/request")

    chat = models.Chat.get_by_id(update.message.chat_id)
    if not chat:
        log.error("Chat not found")
        return

    answer = chat_gpt.get_answer(
        prompt=chat.prompt,
        message=message,
        conversation_id=chat.id,
    )
    max_length = 4096
    parts = [answer[i:i + max_length] for i in range(0, len(answer), max_length)]
    for part in parts:
        await update.message.reply_text(text=part)

async def on_message(update: telegram.Update, context: CallbackContext):
    log.debug("on_message %s", update.message.text)

    if not check_access_to_chat(update):
        return

    chat = models.Chat.get_by_id(update.message.chat_id)
    if chat.mode != "member":
        return

    answer = chat_gpt.get_answer(
        prompt=chat.prompt,
        message=update.message.text,
        conversation_id=chat.id,
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=answer,
    )
