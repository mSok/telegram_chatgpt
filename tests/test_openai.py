from unittest.mock import MagicMock, patch

import pytest

from src.open_ai.chat_gpt import get_answer


@pytest.mark.asyncio
async def test_get_answer():
    """Тест получения ответа от OpenAI"""
    test_prompt = "You are a helpful assistant"
    test_message = "Hello, how are you?"
    test_response = "I'm doing well, thank you for asking!"

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = test_response

    with patch('openai.ChatCompletion.create', return_value=mock_response):
        response = get_answer(test_prompt, test_message, None)

        assert response == test_response

@pytest.mark.asyncio
async def test_get_answer_with_conversation():
    """Тест получения ответа от OpenAI с историей разговора"""
    test_prompt = "You are a helpful assistant"
    test_message = "What's the weather like?"
    test_response = "I don't have access to real-time weather information"
    conversation_id = 12345

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = test_response

    with patch('openai.ChatCompletion.create', return_value=mock_response):
        response = get_answer(test_prompt, test_message, conversation_id)

        assert response == test_response
