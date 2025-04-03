import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from src import config
from src.database import models
from .handlers import (
    set_enable,
    set_disable,
    set_prompt,
    set_default_prompt,
    clear,
    set_mode,
    get_status,
    add_chat_or_user,
    on_message,
    request,
    generate_image,
    button_callback,
)

log = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    """Initialize bot handlers and commands"""
    application.add_handler(CommandHandler("enable", set_enable))
    application.add_handler(CommandHandler("disable", set_disable))
    application.add_handler(CommandHandler("set_prompt", set_prompt))
    application.add_handler(CommandHandler("default_prompt", set_default_prompt))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(CommandHandler("set_mode", set_mode))
    application.add_handler(CommandHandler("status", get_status))
    application.add_handler(CommandHandler("request", request))
    application.add_handler(CommandHandler("add_chat_or_user", add_chat_or_user))
    application.add_handler(CommandHandler("generate_image", generate_image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    # Добавляем обработчик для callback
    application.add_handler(CallbackQueryHandler(button_callback))

    await application.bot.set_my_commands(
        [
            ("request", "Задать вопрос боту"),
            ("set_prompt", "Установить контекст общения"),
            ("default_prompt", "Сбросить в default"),
            ("status", "Статус"),
            ("set_mode", "member встревает во все разговоры, любой другой нет"),
            ("clear", "Очистить историю"),
            ("add_chat_or_user", "Добавить чат или пользователя"),
            ("generate_image", "Сгенерировать изображение по описанию"),
        ]
    )

def start_bot() -> None:
    """Start the bot."""
    log.info("Start BOT")

    # Инициализируем базовые промпты
    # models.ImagePrompt.initialize_default_prompts()

    # Create the Application and pass it your bot's token.
    application = (
        Application.builder().token(config.TELEGRAM_TOKEN).post_init(post_init).build()
    )

    if config.RUN_POOLING:
        log.info("Run bot in pollling mode 🚗")
        application.run_polling()
    else:
        application.run_webhook(
            listen="0.0.0.0",
            port=config.PORT,
            secret_token="ASecretTokenIHaveChangedByNow",
            webhook_url="https://<appname>.herokuapp.com/",
        )
