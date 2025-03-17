import logging
import telegram
from src import config
from src.database import models

log = logging.getLogger(__name__)

def check_access_to_chat(update: telegram.Update, check_admin_rights=False) -> bool:
    """Проверяем доступность бота в чате"""

    if not update.message or not update.message.from_user:
        return False

    if check_admin_rights:
        return (
            models.BotAdmin.is_admin(update.message.from_user.id)
            or update.message.from_user.id == config.TELEGRAM_ADMIN_USER_ID
        )

    if not models.Chat.is_enable(update.message.chat_id):
        log.info(
            "No access chat_id: %s user_id: %s",
            update.message.chat_id,
            update.message.from_user.id,
        )
        return False
    return True