import logging
import random
from collections import defaultdict
from datetime import date

import telegram
from telegram import Update
from telegram.ext import CallbackContext

from src import config
from src.database import models
from src.image_gen import ImageGenerator
from src.open_ai import chat_gpt
from src.tg import utils

from ..utils import check_access_to_chat

log = logging.getLogger(__name__)
fails_by_date = defaultdict(int)
cnt_by_chat = defaultdict(int)

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
    prompt = ' '.join(message.text.split(' ')[1:]).strip()

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

    await message.reply_photo(
        photo=image_data,
        caption="🎨 Что то интересное",
    )


async def generate_image_from_photo(update: Update, context: CallbackContext):
    """Generate an image based on a photo and prompt"""
    log.debug("generate_image_from_photo command")

    if not config.IMAGE_GEN:
        return

    if not check_access_to_chat(update):
        return

    message = update.message

    if not message or not message.chat:
        log.error("Update message or chat is None")
        return

    if cnt_by_chat[f"{message.chat_id}_{date.today()}"] > 100:
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="Упс! ну все все !",
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
        )

    # Check if message contains photo and caption (prompt)
    message_photo = message.photo
    message_caption = message.caption or message.text

    if message.reply_to_message and message.reply_to_message.photo:
        message_photo = message.reply_to_message.photo
        message_caption = message.text


    if not message_caption:
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="Please send a photo with a caption as the prompt for image generation.",
        )
        return

    # Get the photo and prompt
    prompt = message_caption.strip()
    if not prompt.startswith(config.BANANO_PREFIX):
        return
    prompt = utils.remove_any_prefix(prompt, config.BANANO_PREFIX).strip()

    photo_url = None
    if message_photo:
        photo = message_photo[-1] # Get the largest photo
        # Get file URL from Telegram
        file = await context.bot.get_file(photo.file_id)
        photo_url = file.file_path

    # Generate image from photo and prompt
    generator = ImageGenerator()
    image_data = await generator.generate_image_from_photo(prompt, photo_url)

    if not image_data:
        log.debug("Не удалось сгенерировать изображение.")
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="Упс Что то пошло не так",
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
        )
        return

    cnt_by_chat[f"{message.chat_id}_{date.today()}"] += 1
    log.debug(f'''cnt_by_chat={ cnt_by_chat[f"{message.chat_id}_{date.today()}"]}''')

    await message.reply_photo(
        photo=image_data,
        caption=f"🎨 Generated from your photo with prompt: {prompt}",
    )
