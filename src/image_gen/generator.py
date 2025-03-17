import logging
from typing import Optional
from src import config

log = logging.getLogger(__name__)
from huggingface_hub import InferenceClient


class ImageGenerator:
    def __init__(self, api_token: Optional[str] = None):
        """
        Инициализация генератора изображений
        :param api_token: API токен Hugging Face (если не указан, берется из конфига)
        """
        self.api_token = api_token or config.HUGGINGFACE_API_TOKEN
        self.client = InferenceClient(api_key=self.api_token)

    async def generate_image(self, prompt: str) -> Optional[bytes]:
        """
        Генерация изображения по текстовому описанию через Stable Diffusion
        :param prompt: Текстовое описание желаемого изображения
        :return: Байты изображения или None в случае ошибки
        """
        log.debug(f'Prompt for image {prompt}')
        try:
            # Используем прямой POST запрос к API
            response = self.client.post(
                json={
                    "inputs": prompt,
                    "parameters": {
                        "num_inference_steps": 15,  # Минимальное количество шагов
                        "guidance_scale": 4.0,     # Меньшее значение = быстрее, но менее точно следует промпту
                        "width": 512,              # Меньший размер изображения
                        "height": 512,
                    }
                },
                model=config.HUGGINGFACE_MODEL,
                task="text-to-image",
            )

            # Возвращаем байты изображения напрямую
            return response

        except Exception as e:
            log.error(f"Error generating image: {str(e)}")
            return None
