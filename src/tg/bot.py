from collections import defaultdict
from datetime import date
import json
import logging
import random

import telegram
from src import config
from src.constants import BotMode
from src.database import models
from src.open_ai import chat_gpt
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.image_gen import ImageGenerator
from src.database.models import add_chat_to_whitelist

log = logging.getLogger(__name__)
fails_by_date = defaultdict(int)

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

    # % шанс сгенерировать изображение
    if random.random() < chat.img_chance:
        await generate_image(update=update, context=context)


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
    # % шанс сгенерировать изображение
    if random.random() < chat.img_chance:
        await generate_image(update=update, context=context)


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

    if not update.message or not update.message.chat_id:
        log.error("Update message or chat_id is None")
        return

    chat_gpt.clear_conversation(update.message.chat_id)

    return await context.bot.send_message(
        chat_id=update.effective_chat.id if update.effective_chat else update.message.chat_id,
        text="Ok."
    )


async def set_mode(update: telegram.Update, context: CallbackContext):
    log.debug("set_mode command")
    if not check_access_to_chat(update):
        return

    if not update.message or not update.message.text:
        log.error("Update message or text is None")
        return

    message = update.message.text.removeprefix("/set_mode").strip()
    log.debug("set_mode command %s message for %s", message, update.message.chat_id if update.message else "No chat_id")

    if not message in BotMode.__members__:
        return await context.bot.send_message(
            chat_id=update.effective_chat.id if update.effective_chat else (update.message.chat_id if update.message else None),
            text="Only `member` or `request`",
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
        )

    chat_id = update.message.chat_id if update.message else None
    if not chat_id:
        log.error("Chat ID is None")
        return

    chat = models.Chat.get_by_id(chat_id)
    if not chat:
        log.error("Chat not found")
        return

    new_mode = models.Chat.set_mode(chat_id, BotMode(message))

    return await context.bot.send_message(
        chat_id=update.effective_chat.id if update.effective_chat else chat_id,
        text=f"Ok. {new_mode}",
    )


async def get_status(update, context):
    log.debug("get_status command")
    if not update.message or not update.message.chat_id:
        log.error("Update message or chat_id is None")
        return

    chat = models.Chat.get_by_id(update.message.chat_id)
    if not chat:
        log.error("Chat not found")
        return

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
        ensure_ascii=False,
    )

    return await context.bot.send_message(
        chat_id=update.effective_chat.id if update.effective_chat else update.message.chat_id,
        text=f"""<code>{json_data}</code>""",
        parse_mode=telegram.constants.ParseMode.HTML,
    )


async def request_admin_approval(bot, chat_id: int, admin_id: int):
    try:
        chat = await bot.get_chat(chat_id)
        chat_title = chat.title if chat else 'неизвестный чат'
        log.info("Имя чата: %s", chat_title)
    except Exception as e:
        log.error("Ошибка при получении информации о чате: %s", e)
        return

    # Создаем кнопки для подтверждения или отклонения
    keyboard = [
        [
            InlineKeyboardButton("Разрешить", callback_data=f"approve_{chat_id}"),
            InlineKeyboardButton("Отклонить", callback_data=f"deny_{chat_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Создаем ссылку на чат
    chat_link = f"https://t.me/c/{chat_id}"

    # Отправляем сообщение админу
    await bot.send_message(
        chat_id=admin_id,
        text=f"Вы хотите разрешить боту отвечать в чате <a href='{chat_link}'>{chat_title}</a> (ID: {chat_id})?",
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.HTML
    )
    return True


async def add_chat_or_user(update: telegram.Update, context: CallbackContext):
    log.debug("add_chat_or_user command")
    if not check_access_to_chat(update, check_admin_rights=True):
        return

    if not update.message or not update.message.text:
        log.error("Update message or text is None")
        return

    message = update.message.text.removeprefix("/add_chat_or_user").strip()

    chat_id = update.message.chat_id if update.message else None
    if not chat_id:
        log.error("Chat ID is None")
        return

    # Отправляем запрос админу на добавление чата или пользователя
    await request_admin_approval(context.bot, chat_id, config.TELEGRAM_ADMIN_USER_ID)


async def button_callback(update: telegram.Update, context: CallbackContext) -> None:
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
    if callback_data.startswith("approve:"):
        chat_id = callback_data.split(":")[1]
    elif callback_data.startswith("deny:"):
        chat_id = callback_data.split(":")[1]

    if not chat_id:
        log.error("Chat ID is None")
        return

    if callback_data.startswith("approve:"):
        await context.bot.send_message(
            chat_id=chat_id,
            text="✅ Запрос на добавление бота одобрен. Теперь вы можете общаться со мной.",
        )
        await query.edit_message_text(text=f"✅ Запрос на добавление бота в чат {chat_id} одобрен.")
        add_chat_to_whitelist(chat_id)
    elif callback_data.startswith("deny:"):
        await context.bot.send_message(chat_id=chat_id, text="❌ Запрос на добавление бота отклонен.")
        await query.edit_message_text(text=f"❌ Запрос на добавление бота в чат {chat_id} отклонен.")


async def generate_image(update: telegram.Update, context: CallbackContext):
    log.debug("generate_image command")
    if not config.IMAGE_GEN:
        return

    if not check_access_to_chat(update):
        return

    if not update.message or not update.message.text or not update.effective_chat:
        log.error("Update message, text or effective_chat is None")
        return

    # Получаем промпт из сообщения или используем случайный
    prompt = update.message.text.removeprefix("/generate_image").strip()
    if fails_by_date[date.today()] > 3:
        log.info("Закончились попытки на сегодня!")
        return

    if not prompt:
        prompts = list(models.ImagePrompt.select())
        if not prompts:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ В базе данных нет доступных промптов.",
            )
            return

        random_prompt = random.choice(prompts)
        prompt = random_prompt.prompt
    else:
        prompt = chat_gpt.get_answer(
            prompt=config.DEFAULT_PROMPT_IMAGE,
            message=prompt,
            conversation_id=None,
        )
    # Генерируем изображение
    generator = ImageGenerator()
    image_data = await generator.generate_image(prompt)

    if not image_data:
        fails_by_date[date.today()] += 1

        log.debug("Не удалось сгенерировать изображение.")
        return

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=image_data,
        caption=f"🎨 Что то интересное",
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
            # Оставим скрытой командой - только для знающих
            # ("generate_image", "Сгенерировать изображение по описанию"),
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
