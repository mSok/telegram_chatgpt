import logging

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import CallbackContext

from src import config

log = logging.getLogger(__name__)


async def wordle(update: telegram.Update, context: CallbackContext):
    log.info('run wordle')
    keyboard = [[InlineKeyboardButton("Play Wordle", web_app=WebAppInfo(url=f"{config.HOST_URL}/wordle.html"))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Play Wordle:', reply_markup=reply_markup)
