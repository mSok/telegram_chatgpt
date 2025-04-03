import logging
import random
from datetime import date
from collections import defaultdict
import telegram
from telegram.ext import CallbackContext
from telegram import Update

from src import config
from src.database import models
from src.open_ai import chat_gpt
from src.image_gen import ImageGenerator
from ..utils import check_access_to_chat

log = logging.getLogger(__name__)
fails_by_date = defaultdict(int)

async def generate_image(update: Update, context: CallbackContext):
    """Генерация изображения по описанию"""
    log.debug("generate_image command")
    if not config.IMAGE_GEN:
        return

    if not check_access_to_chat(update):
        return

    message = update.message
    if not message or not message.text or not message.chat:
        log.error("Update message, text or chat is None")
        return

    is_command = False
    if '/generate_image' in message.text:
        is_command = True

    # Получаем промпт из сообщения или используем случайный
    prompt = message.text.removeprefix("/generate_image").strip()
    if fails_by_date[date.today()] > 3:
        log.info("Закончились попытки на сегодня!")
        return

    if not prompt:
        prompts = list(models.ImagePrompt.select())
        if not prompts:
            await context.bot.send_message(
                chat_id=message.chat_id,
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
        if is_command:
            await context.bot.send_message(
                chat_id=message.chat_id,
                text="Уууу! Бесплатный генератор не всегда может",
                parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
            )
        return

    await context.bot.send_photo(
        chat_id=message.chat_id,
        photo=image_data,
        caption=f"🎨 Что то интересное",
    )