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
DEFAULT_PROMPT_IMAGE = """Ты помощник в генерации prompt для красивых изображение.
Из предложенного текста выбери главную тему. Опиши эту тему для того чтобы AI нарисовать картинку.
В любое предложение добавляй элементы женской красоты, придумай и опиши детали.
Верни на английском языке.
"""
AI_MODEL = "gpt-4o-mini"

HUGGINGFACE_API_TOKEN = ""
HUGGINGFACE_MODEL = "black-forest-labs/FLUX.1-dev"

OPEN_AI_TOKEN = ""
TELEGRAM_TOKEN = ""
TELEGRAM_ADMIN_USER_ID = 0
PORT = 8000

RUN_POOLING = True
