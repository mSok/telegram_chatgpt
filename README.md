# Telegram GPT Bot

Телеграм-бот, интегрированный с GPT для обработки сообщений и генерации ответов.

## 🚀 Особенности

- Интеграция с Telegram API
- Использование GPT для генерации ответов
- Асинхронная обработка сообщений
- Поддержка Docker
- Тестирование с pytest
- Управление зависимостями через uv

## 📋 Требования

- Python 3.8+
- Docker (опционально)
- Telegram Bot Token
- OpenAI API Key
- uv (для управления зависимостями)

## 🛠 Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/telegram_gpt.git
cd telegram_gpt
```

2. Установите uv (если еще не установлен):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Создайте виртуальное окружение и установите зависимости с помощью uv:
```bash
uv venv
source .venv/bin/activate  # для Linux/Mac
# или
.venv\Scripts\activate  # для Windows
uv pip install -e .
```

4. Создайте файл `.env` и добавьте необходимые переменные окружения:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
```

## 🏃‍♂️ Запуск

### Локальный запуск

```bash
python run.py
```

### Запуск через Docker

```bash
docker-compose up --build
```

## 🧪 Тестирование

```bash
pytest tests/
```

## 📁 Структура проекта

```
telegram_gpt/
├── src/                    # Исходный код
├── tests/                  # Тесты
├── sqlite_db/             # База данных SQLite
├── .env                   # Переменные окружения
├── Dockerfile             # Конфигурация Docker
├── docker-compose.yml     # Конфигурация Docker Compose
├── pyproject.toml         # Зависимости и настройки проекта
└── README.md             # Документация
```

## 🔧 Основные зависимости

- python-telegram-bot==20.1
- openai==0.27.2
- peewee==3.16.0
- aiohttp==3.8.4
- pytest==7.0.1 (для тестирования)

## 📦 Управление зависимостями

Проект использует [uv](https://github.com/astral-sh/uv) для управления зависимостями Python. Это быстрый и современный инструмент, который заменяет pip и virtualenv.

Основные команды:
```bash
# Создание виртуального окружения
uv venv

# Установка зависимостей
uv pip install -e .

# Обновление зависимостей
uv pip install --upgrade -e .
```

## 🤖 Использование бота

1. Найдите бота в Telegram по его username
2. Отправьте команду `/start` для начала работы
3. Отправьте любое сообщение, и бот ответит с помощью GPT

## 📝 Лицензия

MIT License - см. файл [LICENSE](LICENSE) для подробностей.

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для ваших изменений
3. Внесите изменения и создайте pull request

## ⚠️ Примечания для ИИ-агентов

- Проект использует асинхронное программирование
- Основной код находится в директории `src/`
- Тесты расположены в директории `tests/`
- Конфигурация проекта в `pyproject.toml`
- Переменные окружения в `.env`
- Docker-конфигурация в `Dockerfile` и `docker-compose.yml`
