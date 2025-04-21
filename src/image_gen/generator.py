from io import BytesIO
import logging
from typing import Optional

import requests
from src import config
# import replicate
from replicate.client import Client

log = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self, api_token: Optional[str] = None):
        """
        Инициализация генератора изображений
        :param api_token: API токен Hugging Face (если не указан, берется из конфига)
        """
        self.replicate = Client(api_token=api_token or config.REPLICATE_API_TOKEN)


    async def generate_image(self, prompt: str) -> Optional[bytes]:
        """
        Генерация изображения по текстовому описанию через Stable Diffusion
        :param prompt: Текстовое описание желаемого изображения
        :return: Байты изображения или None в случае ошибки
        """
        log.debug(f'Prompt for image {prompt}')

        try:
            # Возвращаем байты изображения напрямую
            response = self.replicate.run(
                config.IMAGE_MODEL,
                input={"prompt": prompt},
            )

        except Exception as e:
            log.error(f"Error generating image: {str(e)}")
            return None

        image_bytes = response.read()  # bytes

        image_io = BytesIO(image_bytes)
        image_io.name = "yahoo.png"  # нужно имя файла

        return image_io
