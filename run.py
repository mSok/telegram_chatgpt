import asyncio
import logging

import click

from src.database import connect_db
from src.tg.bot import start_bot
from src.tg.scripts.load_history import get_messages

log = logging.getLogger(__name__)

@click.group()
def cli():
    pass

@cli.command()
@click.option('--chat-id', required=True, help='ID чата для загрузки сообщений')
def load_history(chat_id):
    """Загрузить историю сообщений из Telegram"""
    log.info(f'Загрузка сообщений из чата {chat_id}')
    asyncio.run(get_messages(chat_id))


@cli.command()
def init_db():
    """Создать таблицы в БД"""
    connect_db()


@cli.command()
def run_bot():
    """Запустить Telegram бота"""
    start_bot()

if __name__ == '__main__':
    cli()
