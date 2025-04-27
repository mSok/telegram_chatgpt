import logging

from src import config
from src.database import models

log = logging.getLogger(__name__)


def connect_db():
    log.info("Connecting DB %s...", config.DB_NAME)
    models.sql_lite_db.connect()
    models.sql_lite_db.create_tables(
        [models.Chat, models.BotAdmin, models.ImagePrompt, models.TGUser, models.ChatHistory],
        safe=True,
    )
