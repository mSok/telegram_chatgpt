import logging
from io import BytesIO

from replicate.client import Client

from src import config

log = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self, api_token: str | None = None):
        """
        Инициализация генератора изображений
        :param api_token: API токен Hugging Face (если не указан, берется из конфига)
        """
        self.replicate = Client(api_token=api_token or config.REPLICATE_API_TOKEN)


    async def generate_image(self, prompt: str) -> bytes | None:
        """
        Генерация изображения по текстовому описанию через Stable Diffusion
        :param prompt: Текстовое описание желаемого изображения
        :return: Байты изображения или None в случае ошибки
        """
        log.debug(f'Prompt for image {prompt}')

        try:
            # Возвращаем байты изображения напрямую
            response = await self.replicate.async_run(
                config.IMAGE_MODEL,
                input={"prompt": prompt},
            )

        except Exception as e:
            log.error(f"Error generating image: {e!s}")
            return None

        image_bytes = response.read()  # bytes

        image_io = BytesIO(image_bytes)
        image_io.name = "yahoo.png"  # нужно имя файла

        return image_io

    async def generate_image_from_photo(self, prompt: str, photo_url: str) -> BytesIO | None:
            """
            Generate an image based on a prompt and input photo using Replicate
            :param prompt: Text prompt for image modification
            :param photo_url: URL of the input image
            :return: BytesIO of the generated image or None in case of error
            """
            log.debug(f'Prompt for image {prompt}, photo URL: {photo_url}')

            try:
                # Prepare input for Replicate model that accepts image and prompt
                input_data = {
                    "prompt": prompt,
                    "image_input": [photo_url]
                }

                response = await self.replicate.async_run(
                    config.IMAGE_TO_IMAGE_MODEL,
                    input=input_data
                )

            except Exception as e:
                log.error(f"Error generating image from photo: {e!s}")
                return None

            # Read the response as bytes
            image_bytes = response.read()  # bytes

            # Create BytesIO object for Telegram
            image_io = BytesIO(image_bytes)
            image_io.name = "generated_image.jpg"  # needs a file name

            return image_io
