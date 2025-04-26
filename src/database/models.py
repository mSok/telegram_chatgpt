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
    img_chance = peewee.FloatField(default=0, help_text="Chance to answer with photo")

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
                "enable": True,
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

class ImagePrompt(BaseModel):
    id = peewee.IntegerField(primary_key=True)
    prompt = peewee.TextField()

    @classmethod
    def initialize_default_prompts(cls):
        """Добавляет базовые промпты в базу данных, если их еще нет"""
        default_prompts = [  # noqa: E501
            "cinematic photograph, medium-format film aesthetic (1.6), high-end film photography (1.8), low-key photography (2.0), raw and unfiltered (1.9), visible grain (1.7), natural imperfections, detailed skin texture, subtle blemishes, realistic skin pores with a natural matte finish (2.0), dramatic highlights and shadows (2.0), fine art photography (1.8), inspired by Helmut Newton (1.9), petite French woman, 151 cm tall (1.9), slender hourglass figure (1.8), long dark messy hair flowing naturally to the small of her back (1.8), seated gracefully on a full-scale dark brown leather Chesterfield sofa, its iconic tufted leather design accentuated by the warm, golden light of a directional antique floor lamp (1.9), minimalist wall behind the sofa with neutral desaturated tones, avoiding yellow hues (1.7), large abstract art mounted above the sofa, subtle and proportional (1.7), illuminated by a single directional light source, the antique floor lamp positioned to the right of the subject (2.0), soft warm golden light casting volumetric beams through the textured air (1.9), dramatic sculptural shadows falling across her figure, the leather sofa, and the rustic hardwood floor (2.0), moody and intimate ambiance with shadowy corners fading into darkness (2.0), black sheer stockings, semi-transparent, clinging lightly to her thighs and calves, accentuating her figure (1.8), natural pubic hair explicitly visible, full and thick, 1980s-style, fully covering her genital area (2.0), pubic hair blending naturally with the lighting, realistic texture and density (2.0), confident yet relaxed seated posture with back straight and hands lightly resting on the sofa’s edge (1.8), cinematic sculptural light interplay between her skin, the sofa leather, and the hardwood floor textures (2.0), timeless fine art aesthetic (2.0), cinematic elegance with warm directional lighting (2.0), moody and intimate atmosphere (2.0).", # noqa: E501
            " A (22.3) year old (woman:1.1) with (dark:1.2) wavy long hair is totally (naked:1.1) on a sandy beach She is only wearing a red BDSM (choker:1.1) and She is (sensual:1.4) and (glistening:1.2). The scene is shot with (Kodakportra1600:1.1) (filmgrain:1.1) (Analogcamera:1.1) (Sharpdetails:1.1) (50mm:1.1)",  # noqa: E501
        ]

        for prompt in default_prompts:
            cls.get_or_create(prompt=prompt)

def add_chat_to_whitelist(chat_id: int) -> None:
    """
    Добавляет чат в белый список разрешенных чатов.

    Args:
        chat_id: ID чата для добавления в белый список
    """
    Chat.set_prompt(chat_id, "Ты чат бот помогающий пользователю и отвечаешь ему на поставленные вопросы.")
