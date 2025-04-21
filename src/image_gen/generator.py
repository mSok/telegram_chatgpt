import logging
from typing import Optional
from src import config
from huggingface_hub import InferenceClient

log = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self, api_token: Optional[str] = None):
        """
        Инициализация генератора изображений
        :param api_token: API токен Hugging Face (если не указан, берется из конфига)
        """
        self.api_token = api_token or config.HUGGINGFACE_API_TOKEN
        self.client = InferenceClient(
            provider="fal-ai",
            api_key=self.api_token
        )

    async def generate_image(self, prompt: str) -> Optional[bytes]:
        """
        Генерация изображения по текстовому описанию через Stable Diffusion
        :param prompt: Текстовое описание желаемого изображения
        :return: Байты изображения или None в случае ошибки
        """
        log.debug(f'Prompt for image {prompt}')

        try:
            # Возвращаем байты изображения напрямую
            return self.client.text_to_image(
                prompt,
                model=config.HUGGINGFACE_MODEL,
            )

        except Exception as e:
            log.error(f"Error generating image: {str(e)}")
            return None
