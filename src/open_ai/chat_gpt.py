import logging
import typing
from collections import defaultdict, deque
from functools import partial

import openai

from src import config

log = logging.getLogger(__name__)
MIN_LEN_RESPONSE = 15
ERROR_MESSAGE = "Something wrong, retry"
CHAT_CONVERSATION = defaultdict(
    partial(deque, iterable=[], maxlen=config.MAX_HISTORY_LEN)
)

openai.api_key = config.OPEN_AI_TOKEN


def get_conversation_by_id(id: int) -> typing.Iterable[dict[str, str]]:
    return CHAT_CONVERSATION[id]


def append_to_conversation(id: int, messages: list[dict[str, str]]):
    for message in messages:
        CHAT_CONVERSATION[id].append(message)
    return CHAT_CONVERSATION[id]


def clear_conversation(id: int):
    CHAT_CONVERSATION[id] = deque(iterable=[], maxlen=config.MAX_HISTORY_LEN)


def get_answer(prompt: str, message: str, conversation_id: int | None) -> str:
    message_text = [
        {
            "role": "system",
            "content": prompt,
        }
    ]
    if conversation_id:
        for conversation_message in get_conversation_by_id(conversation_id):
            message_text.append(conversation_message)

    # Add user message to request
    message_text.append(
        {
            "role": "user",
            "content": message,
        }
    )

    try:
        response = openai.ChatCompletion.create(
            model=config.AI_MODEL,
            messages=message_text,
        )
    except Exception as exc:
        log.error(exc)
        return ERROR_MESSAGE

    result = ""
    for choice in response.choices:
        result += choice.message.content

    result = result.strip()

    log.debug("result: %s", result)
    if len(result) < MIN_LEN_RESPONSE and "No content" in result:
        return ""

    if conversation_id:
        append_to_conversation(
            conversation_id,
            [
                {"role": "user", "content": message},
                {"role": "assistant", "content": result},
            ],
        )

    return result
