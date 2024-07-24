import json
import logging

import telegram
from src import config
from src.constants import BotMode
from src.database import models
from src.open_ai import chat_gpt
from telegram.ext import (Application, CallbackContext, CommandHandler,
                          MessageHandler, filters)

log = logging.getLogger(__name__)


def check_access_to_chat(update: telegram.Update, check_admin_rights=False) -> bool:
    """Проверяем включен ли бот в чате"""

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


async def request(update: telegram.Update, context):
    log.debug("request %s", update.message.text)

    if not check_access_to_chat(update):
        return

    message = update.message.text.removeprefix("/request")

    chat = models.Chat.get_by_id(update.message.chat_id)

    answer = chat_gpt.get_answer(
        prompt=chat.prompt,
        message=message,
        conversation_id=chat.id,
    )
    max_length = 4096
    parts = [answer[i:i + max_length] for i in range(0, len(answer), max_length)]
    for part in parts:
        await update.message.reply_text(text=part)


async def on_message(update, context):
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


async def set_enable(update, context):
    log.debug("enable command")

    if not check_access_to_chat(update, check_admin_rights=True):
        return

    models.Chat.set_state(update.message.chat_id, True)
    chat = models.Chat.get_by_id(update.message.chat_id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=config.DEFAULT_BOT_PROMPT + f"""prompt: {chat.prompt}""",
    )


async def set_disable(update, context):
    log.debug("disable command")
    if not check_access_to_chat(update):
        return
    models.Chat.set_state(update.message.chat_id, False)

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Я отключился. Все пока в этом чате."
    )


async def set_prompt(update, context):
    log.debug("set_prompt command")
    if not check_access_to_chat(update):
        return

    message = update.message.text.removeprefix("/set_prompt")

    new_prompt = models.Chat.set_prompt(update.message.chat_id, message)
    chat_gpt.clear_conversation(update.message.chat_id)

    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"У меня установлен следующий prompt: \n```{new_prompt}```",
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
    )


async def set_default_prompt(update, context):
    log.debug("set_default_prompt command")
    if not check_access_to_chat(update):
        return

    new_prompt = models.Chat.set_prompt(update.message.chat_id, config.DEFAULT_PROMPT)
    chat_gpt.clear_conversation(update.message.chat_id)

    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"У меня установлен следующий prompt: \n```{new_prompt}```",
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
    )


async def clear(update: telegram.Update, context: CallbackContext):
    log.debug("clear command")
    if not check_access_to_chat(update):
        return
    chat_gpt.clear_conversation(update.message.chat_id)

    return await context.bot.send_message(chat_id=update.effective_chat.id, text="Ok.")


async def set_mode(update: telegram.Update, context: CallbackContext):
    log.debug("set_mode command")
    if not check_access_to_chat(update):
        return

    message = update.message.text.removeprefix("/set_mode").strip()
    log.debug("set_mode command %s message for %s", message, update.message.chat_id)

    if not message in BotMode.__members__:
        return await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Only `member` or `request`",
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
        )

    new_mode = models.Chat.set_mode(update.message.chat_id, BotMode(message))

    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Ok. {new_mode}",
    )


async def get_status(update, context):
    log.debug("get_status command")
    chat = models.Chat.get_by_id(update.message.chat_id)

    json_data = json.dumps(
        {
            "enable": chat.enable,
            "mode": chat.mode,
            "prompt": chat.prompt,
            "model": config.AI_MODEL,
            "chat_id": update.message.chat_id,
        },
        indent=4,
        default=str,
    )

    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"""<code>{json_data}</code>""",
        parse_mode=telegram.constants.ParseMode.HTML,
    )


async def post_init(application: Application) -> None:
    application.add_handler(CommandHandler("enable", set_enable))
    application.add_handler(CommandHandler("disable", set_disable))
    application.add_handler(CommandHandler("set_prompt", set_prompt))
    application.add_handler(CommandHandler("default_prompt", set_default_prompt))

    application.add_handler(CommandHandler("clear", clear))

    application.add_handler(CommandHandler("set_mode", set_mode))
    application.add_handler(CommandHandler("status", get_status))
    application.add_handler(CommandHandler("request", request))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    await application.bot.set_my_commands(
        [
            ("request", "Задать вопрос боту"),
            ("set_prompt", "Установить контекст общения"),
            ("default_prompt", "Сбросить в default"),
            ("status", "Статус"),
            ("set_mode", "member встревает во все разговоры, любой другой нет"),
            ("clear", "Очистить историю"),
        ]
    )


def start_bot() -> None:
    """Start the bot."""
    log.info("Start BOT")
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
