import logging
import os

from telethon.sync import Message, TelegramClient

from src.database import models

log = logging.getLogger(__name__)

def load_tg_client() -> TelegramClient:
    # Загружаем переменные окружения

    api_id = int(os.getenv('SCRIPT_TELEGRAM_API_ID'))
    api_hash = os.getenv('SCRIPT_TELEGRAM_API_HASH')
    return TelegramClient("session_name", api_id, api_hash)


async def _save_history(message: Message, client: TelegramClient) -> tuple[bool, bool]:
    user_id = message.from_id.user_id
    user_added = False
    msg_added = False

    if not (tg_user := models.TGUser.get_or_none(id=user_id)):
        user_entity = await client.get_entity(user_id)
        full_name = ' '.join(filter(None, [user_entity.first_name, user_entity.last_name]))
        tg_user, _  = models.TGUser.get_or_create(
            id=user_id,
            defaults={
                'name': user_entity.username,
                'username': user_entity.username,
                'is_bot': user_entity.bot,
                'full_name': full_name,
                'first_name': user_entity.first_name,
                'last_name': user_entity.last_name,
            },
        )
        log.info('User added %s', tg_user)
        user_added = True

    reply_history_msg = None
    if message.reply_to_msg_id:
        reply_history_msg = models.ChatHistory.get_or_none(chat_id=message.chat_id, message_id=message.reply_to_msg_id)

    if not models.ChatHistory.get_or_none(
        message_id=message.id,
        chat=message.chat_id,
    ) and message.text:
        models.ChatHistory.create(
            created_at=message.date,
            chat = message.chat_id,
            message_id = message.id,
            text = message.text,
            from_user = tg_user,
            reply_to = reply_history_msg if reply_history_msg else None
        )
        log.info(f'Message added {message.text[:20]}...')
        msg_added = True

    return (msg_added, user_added)

async def get_messages(chat_id):
    client = load_tg_client()
    phone = os.getenv('SCRIPT_TELEGRAM_PHONE')
    password = os.getenv('SCRIPT_TELEGRAM_PASSWORD')

    client.start(phone=phone, password=password)
    async with client:
        messages = await client.get_messages(int(chat_id), limit=200)
        messages.reverse()

        cnt_msg = 0
        cnt_users = 0

        for msg in messages:
            m, u = await _save_history(message=msg, client=client)
            cnt_msg += m
            cnt_users += u

        log.info(f'Обработка закончена: {cnt_msg=}, {cnt_users=}')
