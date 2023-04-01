import logging
import logging.config
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

LOG_SETTINGS = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {
            "()": "logging.Formatter",
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        }
    },
    "handlers": {"default": {"class": "logging.StreamHandler", "formatter": "default"}},
    "loggers": {
        "src": {"level": LOG_LEVEL, "handlers": ["default"]},
    },
}


logging.config.dictConfig(LOG_SETTINGS)
# apply logging level for already loaded loggers
logging.getLogger().setLevel(LOG_LEVEL)
