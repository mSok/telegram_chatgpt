import logging

import telegram
from telegram.ext import CallbackContext

from src.database import models
from src.open_ai import chat_gpt

from ..utils import check_access_to_chat

log = logging.getLogger(__name__)


def save_history(message: telegram.Message):
    user = message.from_user
    tg_user, _ = models.TGUser.get_or_create(
        id=user.id,
        defaults={
            'name': user.name,
            'username': user.username,
            'is_bot': user.is_bot,
            'full_name': user.full_name,
            'first_name': user.first_name,
            'last_name': user.last_name,
        },
    )


    return models.ChatHistory.create(
        chat = message.chat_id,
        message_id = message.id,
        text = message.text,
        from_user = tg_user,
        reply_to = save_history(message.reply_to_message) if message.reply_to_message else None
    )


async def request(update: telegram.Update, context: CallbackContext):
    log.debug("request %s", update.message.text if update.message else "No message")

    if not check_access_to_chat(update):
        return

    if not update.message or not update.message.text:
        log.error("Update message or text is None")
        return

    save_history(update.message)

    # вырезаем команду /request
    message = ' '.join(update.message.text.split(' ')[1:]).strip()

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
    save_history(update.message)

    chat = models.Chat.get_by_id(update.message.chat_id)
    if chat.mode != "member":
        return

    answer = chat_gpt.get_answer(
        prompt=chat.prompt,
        message=update.message.text,
        conversation_id=chat.id,
    )

    await update.message.reply_text(text=answer)
