import logging

from telegram import Update
from telegram.ext import CallbackContext

from src.database.models import add_chat_to_whitelist

log = logging.getLogger(__name__)

async def button_callback(update: Update, context: CallbackContext) -> None:
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    if not query:
        log.error("Callback query is None")
        return

    await query.answer()
    callback_data = query.data
    if not callback_data:
        log.error("Callback data is None")
        return

    chat_id = None
    if callback_data.startswith(("approve_", "deny_")):
        chat_id = callback_data.split("_")[1]

    if not chat_id:
        log.error("Chat ID is None")
        return
    try:
        chat_id = int(chat_id)
    except Exception as exc:
        log.error("Chat ID Error %s", exc)
        return

    if callback_data.startswith("approve_"):
        await context.bot.send_message(
            chat_id=chat_id,
            text="✅ Запрос на добавление бота одобрен. Теперь вы можете общаться со мной.",
        )
        await query.edit_message_text(text=f"✅ Запрос на добавление бота в чат {chat_id} одобрен.")
        add_chat_to_whitelist(chat_id)
    elif callback_data.startswith("deny_"):
        await context.bot.send_message(chat_id=chat_id, text="❌ Запрос на добавление бота отклонен.")
        await query.edit_message_text(text=f"❌ Запрос на добавление бота в чат {chat_id} отклонен.")
