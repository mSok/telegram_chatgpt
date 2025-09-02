import click
from scripts.load_history import client, get_messages

from .bot import start_bot


@click.group()
def cli():
    pass

@cli.command()
def load_history():
    """Загрузить историю сообщений из Telegram"""
    with client:
        client.loop.run_until_complete(get_messages())

@cli.command()
def run_bot():
    """Запустить Telegram бота"""
    start_bot()

if __name__ == '__main__':
    cli()
