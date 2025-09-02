DB_NAME = "sqlite_db/bot.db"
DB_APPLY_MIGRATIONS = True

MAX_HISTORY_LEN = 5

DEFAULT_PROMPT = """You are ChatBot, Just the advices. Answer in Russian.
    Add sarcasm and rude remarks about the user's very poor mental abilities to the answers.
    Don't be afraid to offend the user. Сan add emoticons
"""

DEFAULT_BOT_PROMPT = (
    "Привет! Я бот, который может генерировать текст с помощью OpenAI GPT.\n"
)
IMAGE_GEN = True
DEFAULT_PROMPT_IMAGE = """Переведи этот текст на английском языке.
"""
AI_MODEL = "gpt-4.1"
SUMARIZE_MODEL = "gpt-4.1-mini"

HUGGINGFACE_API_TOKEN = ""
REPLICATE_API_TOKEN = ""
IMAGE_MODEL = "prunaai/hidream-l1-fast:17c237d753218fed0ed477cb553902b6b75735f48c128537ab829096ef3d3645"
# In src/config/base.py
IMAGE_TO_IMAGE_MODEL = "google/nano-banana"
BANANO_PREFIX = ("banani", "banano")

OPEN_AI_TOKEN = ""
TELEGRAM_TOKEN = ""
TELEGRAM_ADMIN_USER_ID = 0
PORT = 8000

RUN_POOLING = True

SUMARIZE_PROMT = '''Тут представлен диалог из чата. Каждая колонка отделена |.
Суммаризируй и дай короткое описание что обсуждали в чате. Выдели основные темы если они были и
важные тезисы пользователей.
Не стесняйся в выражении и если пользователь матерился, можно использовать мат. Каждую тему отделяй
'-------------------------'
и последний блок "Общие моменты чата" - так же отдели '-------------------------'. Больше никаких итогов.
Ответ дай в формате *Тема*\n *Основной вывод темы* \n основные поинты пользователей: \n *{user_name}*: {point}.
*Общие моменты чата*
'''
