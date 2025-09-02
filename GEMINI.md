# GEMINI.md

## Project Overview

This project is a Telegram bot that uses the OpenAI GPT API to generate responses to user messages. The bot is built with Python and uses the `python-telegram-bot` library. It's designed to be asynchronous and can be run locally or with Docker. The project uses `peewee` for database interaction and `uv` for dependency management.

The main application logic is in `src/tg/bot.py`, which sets up the bot and its command handlers. The handlers themselves are defined in the `src/tg/handlers/` directory. The `run.py` script provides a command-line interface for running the bot, initializing the database, and loading chat history.

## Building and Running

### Prerequisites

*   Python 3.10+
*   `uv` package manager
*   Telegram Bot Token
*   OpenAI API Key

### Local Development

1.  **Install dependencies:**
    ```bash
    uv pip install -e .
    ```

2.  **Set up environment variables:**
    Create a `.env` file in the root directory with the following content:
    ```
    TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>
    OPENAI_API_KEY=<your_openai_api_key>
    ```

3.  **Initialize the database:**
    ```bash
    python run.py init-db
    ```

4.  **Run the bot:**
    ```bash
    python run.py run-bot
    ```

### Docker

1.  **Build and run the container:**
    ```bash
    docker-compose up --build
    ```

### Testing

Run the tests using `pytest`:

```bash
pytest tests/
```

## Development Conventions

*   **Linting:** The project uses `ruff` for linting. The configuration is in `pyproject.toml`.
*   **Formatting:** The project uses `black` for code formatting.
*   **Dependencies:** Dependencies are managed with `uv` and are listed in `pyproject.toml`.
*   **Database:** The project uses `peewee` as an ORM for interacting with a SQLite database. Database models are defined in `src/database/models.py`.
*   **Asynchronous Code:** The project uses `asyncio` for asynchronous operations, particularly in the Telegram bot handlers.
*   **Command-line Interface:** The `run.py` script uses `click` to create a command-line interface.
