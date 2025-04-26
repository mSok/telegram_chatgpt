from collections import defaultdict, deque
from functools import partial
from unittest import mock

import pytest

from src.open_ai import chat_gpt


@pytest.fixture
def chat_conversation():

    new = defaultdict(
        partial(deque, iterable=[], maxlen=2)
    )
    with mock.patch('src.open_ai.chat_gpt.CHAT_CONVERSATION', new):
        yield new



async def test_conversation__append():
    chat_gpt.append_to_conversation(0, [{"role": "system", "content": "system"}])

    assert len(chat_gpt.CHAT_CONVERSATION) == 1
    assert len(chat_gpt.CHAT_CONVERSATION[0]) == 1

    chat_gpt.append_to_conversation(
        0,
        [
            {"role": "user", "content": 'message'},
            {"role": "assistant", "content": 'result'},
        ],
    )
    assert len(chat_gpt.CHAT_CONVERSATION[0]) == 3
    assert list(chat_gpt.CHAT_CONVERSATION[0]) == [
        {'role': 'system', 'content': 'system'},
        {'role': 'user', 'content': 'message'},
        {'role': 'assistant', 'content': 'result'}
    ]
