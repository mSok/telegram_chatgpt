import http.server
import json
import logging
import socketserver
from datetime import date as _date
from urllib.parse import parse_qs, urlparse

from src.database.migrations_runner import run_migrations
from src.database.models import (
    Chat,
    TGUser,
    WordleAttempt,
    WordleDay,
)

PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="web", **kwargs)

    def _send_json(self, status_code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/wordle/today":
            try:
                query = parse_qs(parsed.query)
                chat_id = int(query.get("chat_id", [0])[0])
                user_id = int(query.get("user_id", [0])[0])

                if not chat_id or not user_id:
                    return self._send_json(400, {"error": "chat_id и user_id обязательны"})

                today = _date.today()
                day = WordleDay.get_or_pick_today()

                # ensure chat and user exist for FKs (minimal upsert)
                chat, _ = Chat.get_or_create(id=chat_id, defaults={"enable": False})
                user, _ = TGUser.get_or_create(
                    id=user_id,
                    defaults={
                        "name": str(user_id),
                        "username": "",
                        "is_bot": False,
                    },
                )

                attempts_q = (
                    WordleAttempt.select()
                    .where(
                        (WordleAttempt.date == today)
                        & (WordleAttempt.chat == chat)
                        & (WordleAttempt.user == user)
                    )
                    .order_by(WordleAttempt.attempt_number)
                )
                attempts = list(attempts_q)
                attempts_made = len(attempts)
                has_win = any(a.is_win for a in attempts)
                is_finished = has_win or attempts_made >= 6

                # Не раскрываем слово в случае проигрыша и вообще не отдаем слово наружу
                return self._send_json(
                    200,
                    {
                        "date": str(day.date),
                        "max_attempts": 6,
                        "attempts_made": attempts_made,
                        "is_finished": is_finished,
                        "has_win": has_win,
                    },
                )
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/wordle/guess":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
                data = json.loads(raw.decode("utf-8"))

                guess = (data.get("guess") or "").strip().lower()
                chat_id = int(data.get("chat_id") or 0)
                user_id = int(data.get("user_id") or 0)
                username = (data.get("username") or "").strip()

                if not chat_id or not user_id or not guess:
                    return self._send_json(400, {"error": "chat_id, user_id и guess обязательны"})
                if len(guess) != 5:
                    return self._send_json(400, {"error": "Слово должно быть из 5 букв"})

                day = WordleDay.get_or_pick_today()
                today = day.date

                # ensure chat and user
                chat, _ = Chat.get_or_create(id=chat_id, defaults={"enable": False})
                user, created = TGUser.get_or_create(
                    id=user_id,
                    defaults={
                        "name": username or str(user_id),
                        "username": username,
                        "is_bot": False,
                    },
                )
                # обновим username, если изменился
                if (not created) and username and (user.username != username):
                    user.username = username
                    user.name = username
                    user.save()

                # already finished?
                attempts_q = (
                    WordleAttempt.select()
                    .where(
                        (WordleAttempt.date == today)
                        & (WordleAttempt.chat == chat)
                        & (WordleAttempt.user == user)
                    )
                    .order_by(WordleAttempt.attempt_number)
                )
                attempts = list(attempts_q)
                attempts_made = len(attempts)
                if any(a.is_win for a in attempts):
                    return self._send_json(
                        200,
                        {
                            "error": None,
                            "message": "Уже угадано сегодня",
                            "attempts_made": attempts_made,
                            "is_finished": True,
                            "has_win": True,
                            "tiles": None,
                        },
                    )
                if attempts_made >= 6:
                    return self._send_json(
                        200,
                        {
                            "error": None,
                            "message": "Попытки на сегодня закончились",
                            "attempts_made": attempts_made,
                            "is_finished": True,
                            "has_win": False,
                            "tiles": None,
                        },
                    )

                secret = day.word

                # вычисляем плитки
                tiles = []
                for i in range(5):
                    letter = guess[i]
                    if letter == secret[i]:
                        tiles.append("correct")
                    elif letter in secret:
                        tiles.append("present")
                    else:
                        tiles.append("absent")

                is_win = guess == secret
                attempt_number = attempts_made + 1

                WordleAttempt.create(
                    date=today,
                    chat=chat,
                    user=user,
                    username=username or user.username,
                    attempt_number=attempt_number,
                    guess=guess,
                    is_win=is_win,
                )

                is_finished = is_win or attempt_number >= 6
                return self._send_json(
                    200,
                    {
                        "attempts_made": attempt_number,
                        "is_finished": is_finished,
                        "has_win": is_win,
                        "tiles": tiles,
                    },
                )
            except Exception as exc:
                return self._send_json(500, {"error": str(exc)})

        return super().do_POST()

def run_web_server():
    # применим миграции перед стартом сервера
    try:
        run_migrations()
    except Exception as exc:
        # Не валим сервер, но логично вывести ошибку
        logging.getLogger(__name__).exception("Migrations error: %s", exc)

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
