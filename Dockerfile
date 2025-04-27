FROM python:3.10
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /opt

ENV PYTHONPATH="." \
    PATH="/opt/.venv/bin:$PATH" \
    TZ="UTC"


# Сначала копируем только файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости
RUN uv sync --frozen --no-install-project --no-python-downloads && \
    uv cache clean

# Копируем остальные файлы проекта
COPY . .

ENTRYPOINT [ "uv", "run", "run.py", "run-bot" ]
