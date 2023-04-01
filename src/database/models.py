from datetime import datetime

import peewee
from peewee import Model
from playhouse.sqlite_ext import SqliteExtDatabase

from src import config
from src.constants import BotMode

sql_lite_db = SqliteExtDatabase(
    config.DB_NAME, regexp_function=True, timeout=3, pragmas={"journal_mode": "wal"}
)


class BaseModel(Model):
    class Meta:
        database = sql_lite_db


class Chat(BaseModel):
    id = peewee.IntegerField(primary_key=True)
    created_at = peewee.DateTimeField(default=datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.now)
    enable = peewee.BooleanField(default=False, help_text="Bot state in current chat")
    last_user_changed = peewee.CharField(
        null=True, help_text="Who last change enable state"
    )
    mode = peewee.CharField(default=BotMode.member.value, help_text="Bot mode")

    prompt = peewee.TextField(default=config.DEFAULT_PROMPT)

    @classmethod
    def is_enable(cls, chat_id: int) -> bool:
        return bool(cls.get_or_none(cls.id == chat_id))

    @classmethod
    def set_state(cls, id: int, state: bool) -> bool:
        chat, is_new = cls.get_or_create(
            id=id,
            defaults={
                "enable": state,
                "prompt": config.DEFAULT_PROMPT,
            },
        )
        if not is_new:
            chat.enable = state
            chat.save()

        return chat.enable

    @classmethod
    def set_mode(cls, id: int, mode: BotMode) -> bool:
        chat, is_new = cls.get_or_create(
            id=id,
            defaults={
                "enable": False,
                "prompt": config.DEFAULT_PROMPT,
                "mode": mode.value,
            },
        )
        if not is_new:
            chat.mode = mode.value
            chat.save()

        return chat.mode

    @classmethod
    def set_prompt(cls, id: int, prompt: str) -> str:
        prompt = prompt or config.DEFAULT_PROMPT

        chat, is_new = cls.get_or_create(
            id=id,
            defaults={
                "enable": False,
                "prompt": prompt,
            },
        )
        if not is_new:
            chat.prompt = prompt
            chat.save()

        return chat.prompt


class BotAdmin(BaseModel):
    id = peewee.IntegerField(primary_key=True)
    name = peewee.CharField()

    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        return bool(cls.get_or_none(cls.id == user_id))
