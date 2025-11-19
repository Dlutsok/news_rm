"""
KIE AI Nano Banana Image Generation Client
Клиент для генерации медицинских изображений через KIE AI (Google Gemini 2.5 Flash)
"""

import os
import json
import base64
import logging
import time
import asyncio
from typing import Dict, Optional
import httpx
import requests
from httpx import HTTPStatusError, TimeoutException

logger = logging.getLogger(__name__)


class KieNanoBananaClient:
    """
    Асинхронный клиент для работы с KIE AI Nano Banana API

    Особенности:
    - Text-to-Image генерация через Google Gemini 2.5 Flash
    - Асинхронные операции для высокой производительности
    - Автоматический polling до завершения задачи
    - Retry логика с exponential backoff
    - Обработка rate limits (429 ошибок)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.kie.ai/api/v1",
        timeout: int = 300,
        max_poll_attempts: int = 60,
        poll_interval: int = 5
    ):
        """
        Инициализация клиента

        Args:
            api_key: KIE AI API ключ
            base_url: Базовый URL API
            timeout: Таймаут для HTTP запросов (секунды)
            max_poll_attempts: Максимальное количество попыток polling
            poll_interval: Интервал между polling запросами (секунды)
        """
        if not api_key:
            raise ValueError("KIE API key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_poll_attempts = max_poll_attempts
        self.poll_interval = poll_interval

        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        logger.info(f"KieNanoBananaClient initialized (base_url: {base_url})")

    async def create_task(self, prompt: str, image_urls: Optional[list] = None) -> str:
        """
        Создает задачу генерации изображения

        Args:
            prompt: Текстовое описание для генерации
            image_urls: Список URL для image-to-image редактирования (опционально)

        Returns:
            task_id: Идентификатор созданной задачи

        Raises:
            HTTPError: При ошибках HTTP
            ValueError: При некорректном ответе
        """
        endpoint = f"{self.base_url}/jobs/createTask"

        # Выбор модели в зависимости от наличия входных изображений
        model = "google/nano-banana-edit" if image_urls else "google/nano-banana"

        payload = {
            "model": model,
            "input": {
                "prompt": prompt,
                "output_format": "png",
                "image_size": "16:9"
            }
        }

        if image_urls:
            payload["input"]["image_urls"] = image_urls

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(endpoint, headers=self.headers, json=payload)
                response.raise_for_status()

                result = response.json()
                logger.info(f"KIE API response: {result}")

                # API возвращает: {"code": 200, "message": "success", "data": {"taskId": "..."}}
                if result.get("code") != 200:
                    error_msg = result.get("message", "Unknown error")
                    logger.error(f"KIE API error: {error_msg}")
                    raise ValueError(f"KIE API error: {error_msg}")

                data = result.get("data", {})
                task_id = data.get("taskId")

                if not task_id:
                    logger.error(f"No taskId in response. Full response: {result}")
                    raise ValueError(f"No taskId in response data")

                logger.info(f"Task created: {task_id} (model: {model})")
                return task_id

            except HTTPStatusError as e:
                status_code = e.response.status_code
                error_detail = e.response.text

                if status_code == 401:
                    logger.error("Authentication failed: Invalid API key")
                    raise ValueError("Invalid KIE API key")
                elif status_code == 402:
                    logger.error("Payment required: Insufficient credits")
                    raise ValueError("Insufficient KIE credits")
                elif status_code == 429:
                    logger.warning("Rate limit exceeded")
                    raise
                else:
                    logger.error(f"HTTP {status_code}: {error_detail}")
                    raise

    async def get_task_status(self, task_id: str) -> Dict:
        """
        Получает статус задачи

        Args:
            task_id: Идентификатор задачи

        Returns:
            Словарь с информацией о задаче
        """
        endpoint = f"{self.base_url}/jobs/recordInfo"
        params = {"taskId": task_id}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()

            result = response.json()

            # API возвращает: {"code": 200, "data": {...}}
            if result.get("code") != 200:
                error_msg = result.get("message", "Unknown error")
                logger.error(f"KIE API error getting task status: {error_msg}")
                raise ValueError(f"KIE API error: {error_msg}")

            return result.get("data", {})

    async def wait_for_completion(self, task_id: str) -> Dict:
        """
        Ожидает завершения задачи с периодическим опросом

        Args:
            task_id: Идентификатор задачи

        Returns:
            Финальная информация о завершенной задаче

        Raises:
            TimeoutError: Если задача не завершилась за отведенное время
            RuntimeError: Если задача завершилась с ошибкой
        """
        attempts = 0
        start_time = time.time()

        logger.info(f"Waiting for task completion: {task_id}")

        while attempts < self.max_poll_attempts:
            try:
                task_info = await self.get_task_status(task_id)
                # API возвращает поле "state": "success", "fail", "waiting", "generating", etc.
                status = task_info.get("state", "unknown")

                elapsed = int(time.time() - start_time)
                logger.debug(f"  [{attempts + 1}/{self.max_poll_attempts}] Status: {status} (elapsed: {elapsed}s)")

                if status == "success":
                    logger.info(f"Task completed successfully: {task_id} (took {elapsed}s)")
                    return task_info

                elif status == "fail":
                    error_msg = task_info.get("failMsg", "Unknown error")
                    error_code = task_info.get("failCode", "N/A")
                    logger.error(f"Task failed: {task_id} - {error_code}: {error_msg}")
                    raise RuntimeError(f"Image generation failed ({error_code}): {error_msg}")

                else:
                    # Статусы "waiting", "generating", etc - продолжаем ждать
                    await asyncio.sleep(self.poll_interval)
                    attempts += 1

            except HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limit - увеличиваем интервал
                    wait_time = self.poll_interval * 2
                    logger.warning(f"Rate limit during polling, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    attempts += 1
                else:
                    raise

        elapsed = int(time.time() - start_time)
        raise TimeoutError(
            f"Task {task_id} did not complete in {elapsed}s "
            f"({self.max_poll_attempts} attempts)"
        )

    def _extract_image_bytes(self, task_info: Dict) -> bytes:
        """
        Извлекает image bytes из ответа API

        Args:
            task_info: Информация о завершенной задаче

        Returns:
            Image bytes (PNG format)

        Raises:
            ValueError: Если не удалось извлечь изображение
        """
        # API возвращает resultJson: "{\"resultUrls\":[\"https://...\"]}"
        result_json_str = task_info.get("resultJson")

        if not result_json_str:
            logger.error(f"No resultJson in task_info: {task_info}")
            raise ValueError("No resultJson in API response")

        try:
            result_data = json.loads(result_json_str)
            result_urls = result_data.get("resultUrls", [])

            if not result_urls:
                raise ValueError("No resultUrls in resultJson")

            image_url = result_urls[0]
            logger.info(f"Downloading image from URL: {image_url}")

            # Загружаем изображение по URL
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            image_bytes = response.content
            logger.debug(f"Downloaded image ({len(image_bytes)} bytes)")
            return image_bytes

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse resultJson: {e}")
            raise ValueError(f"Invalid resultJson format: {e}")
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            raise ValueError(f"Failed to download image: {e}")

    async def generate_image(
        self,
        prompt: str,
        image_urls: Optional[list] = None,
        max_retries: int = 3
    ) -> bytes:
        """
        Полный цикл генерации изображения с retry логикой

        Args:
            prompt: Текстовое описание для генерации
            image_urls: Список URL для редактирования (опционально)
            max_retries: Максимальное количество попыток при ошибках

        Returns:
            Image bytes (PNG format)

        Raises:
            Exception: При неудачной генерации после всех попыток
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                # Шаг 1: Создание задачи
                task_id = await self.create_task(prompt, image_urls=image_urls)

                # Шаг 2: Ожидание завершения
                task_info = await self.wait_for_completion(task_id)

                # Шаг 3: Извлечение изображения
                image_bytes = self._extract_image_bytes(task_info)

                logger.info(f"Image generated successfully ({len(image_bytes)} bytes)")
                return image_bytes

            except HTTPStatusError as e:
                status_code = e.response.status_code

                if status_code == 429:
                    # Rate limit - exponential backoff
                    wait_time = (2 ** attempt) * 5  # 5, 10, 20 секунд
                    logger.warning(f"Rate limit exceeded, retry {attempt + 1}/{max_retries} after {wait_time}s")
                    await asyncio.sleep(wait_time)
                    last_error = e
                    continue

                elif status_code in [401, 402]:
                    # Критические ошибки - не retry
                    raise

                else:
                    # Остальные HTTP ошибки - retry
                    logger.error(f"HTTP {status_code} on attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        last_error = e
                        continue
                    raise

            except TimeoutError as e:
                logger.error(f"Timeout on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    last_error = e
                    continue
                raise

            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}/{max_retries}: {e}")
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
                    continue
                raise

        # Все попытки исчерпаны
        logger.error(f"Failed to generate image after {max_retries} attempts")
        raise last_error or RuntimeError("Image generation failed")


# Singleton instance для переиспользования
_kie_client_instance: Optional[KieNanoBananaClient] = None


def get_kie_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: Optional[int] = None
) -> KieNanoBananaClient:
    """
    Получить singleton instance KIE клиента

    Args:
        api_key: KIE API ключ (по умолчанию из env)
        base_url: Base URL (по умолчанию из env или дефолтный)
        timeout: Timeout (по умолчанию из env или 300s)

    Returns:
        KieNanoBananaClient instance
    """
    global _kie_client_instance

    if _kie_client_instance is None:
        api_key = api_key or os.getenv("KIE_API_KEY")
        base_url = base_url or os.getenv("KIE_API_BASE_URL", "https://api.kie.ai/api/v1")
        timeout = timeout or int(os.getenv("KIE_TIMEOUT", "300"))

        _kie_client_instance = KieNanoBananaClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )

    return _kie_client_instance
