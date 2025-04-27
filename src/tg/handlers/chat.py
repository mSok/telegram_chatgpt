import logging

import telegram
from telegram.ext import CallbackContext

from src import config
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

def split_message(msg: str, *, with_photo: bool) -> list[str]:
    """Split the text into parts considering Telegram limits."""
    parts = []
    while msg:
        # Determine the maximum message length based on
        # with_photo and whether it's the first iteration
        # (photo is sent only with the first message).
        if parts:
            max_msg_length = 4096
        elif with_photo:
            max_msg_length = 1024
        else:
            max_msg_length = 4096

        if len(msg) <= max_msg_length:
            # The message length fits within the maximum allowed.
            parts.append(msg)
            break

        # Cut a part of the message with the maximum length from msg
        # and find a position for a break by a newline character.
        part = msg[:max_msg_length]
        first_ln = part.rfind("\n")

        if first_ln != -1:
            # Newline character found.
            # Split the message by it, excluding the character itself.
            new_part = part[:first_ln]
            parts.append(new_part)

            # Trim msg to the length of the new part
            # and remove the newline character.
            msg = msg[first_ln + 1 :]
            continue

        # No newline character found in the message part.
        # Try to find at least a space for a break.
        first_space = part.rfind(" ")

        if first_space != -1:
            # Space character found.
            # Split the message by it, excluding the space itself.
            new_part = part[:first_space]
            parts.append(new_part)

            # Trimming msg to the length of the new part
            # and removing the space.
            msg = msg[first_space + 1 :]
            continue

        # No suitable place for a break found in the message part.
        # Add the current part and trim the message to its length.
        parts.append(part)
        msg = msg[max_msg_length:]

    return parts

async def send_long_message(message: telegram.Message, text: str, parse_mode: str = 'Markdown'):

    for part in split_message(text, with_photo=False):
        await message.reply_text(
            text=part,  # Отрендерить обратно в строку
            parse_mode='Markdown'  # Указываем, что формат Markdown
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
    await send_long_message(update.message, answer)

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

    await send_long_message(update.message, answer)


async def tldr(update: telegram.Update, context: CallbackContext):
    if not check_access_to_chat(update):
        return
    log.info('run tldr')
    # remove command
    messages = update.message.text.split(' ')[1:]
    if messages:
        try:
            log_cnt = int(messages[0])
        except ValueError:
            log_cnt = 200

        if len(messages) > 1:
            try:
                chat_id = int(messages[1])
            except ValueError:
                chat_id = update.message.chat_id

    log.info(f'tldr {chat_id=}, {log_cnt=}')
    history = list(
        models.ChatHistory.select(models.ChatHistory, models.TGUser)
        .join(models.TGUser)
        .where(
            models.ChatHistory.chat_id==chat_id,
        ).order_by(
            models.ChatHistory.created_at.desc()
        ).limit(log_cnt)
    )

    history.reverse()
    _columns = [
        'id',
        'reply_to_id',
        'from_user.username',
        'created_at',
        'text',
    ]

    rows = [' | '.join(_columns)]
    for row in history:
        values = [str(models.get_attr(row, col)) for col in _columns]
        rows.append(' | '.join(values))


    answer = chat_gpt.get_answer(
        prompt=config.SUMARIZE_PROMT,
        message='\\n'.join(rows),
        conversation_id=None,
    )

    await send_long_message(update.message, answer)
