import os
import uuid
from pathlib import Path
from typing import Optional
import logging

from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.config import settings
from api.dependencies import get_current_user_optional, get_current_user
from database.models import User
from services.kie_image_client import get_kie_client

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., description="Текстовый промпт для генерации изображения")


class GenerateImageResponse(BaseModel):
    image_url: str
    model_used: str = "kie-nano-banana"
    success: bool = True
    message: str = "Изображение успешно сгенерировано"


# Настройки для хранения изображений
STORAGE_DIR = Path(settings.BASE_DIR) / "storage" / "images"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/health")
async def image_service_health():
    """Проверка здоровья сервиса генерации изображений"""
    return {
        "status": "healthy",
        "service": "image-generation",
        "provider": "kie-nano-banana",
        "api_key_configured": bool(settings.KIE_API_KEY)
    }


@router.post("/generate", response_model=GenerateImageResponse)
async def generate_image(
    request: Request,
    body: GenerateImageRequest,
    current_user: User = Depends(get_current_user_optional)
):
    """
    Генерация изображения с помощью KIE AI Nano Banana (Google Gemini 2.5 Flash)

    Nano Banana - это передовая AI-модель для генерации медицинских изображений
    с высокой степенью реалистичности и точности.
    """
    try:
        # Проверяем доступность API ключа
        if not settings.KIE_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="KIE_API_KEY не настроен. Пожалуйста, добавьте ключ в .env файл."
            )

        # Получаем KIE клиент
        try:
            kie_client = get_kie_client()
        except ValueError as e:
            logger.error(f"Ошибка инициализации KIE клиента: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Не удалось инициализировать KIE API клиент: {str(e)}"
            )

        # Промпт приходит уже готовым (на английском) от generate_image_prompt
        # Никаких дополнительных модификаций не требуется
        prompt = body.prompt

        username = current_user.username if current_user else 'anonymous'
        logger.info(f"Генерируем изображение для пользователя {username}: {prompt[:100]}...")

        # Генерация изображения через KIE AI
        image_bytes = await kie_client.generate_image(prompt)

        if not image_bytes:
            raise RuntimeError("Пустой ответ от KIE API")

        # Сохранение файла (PNG формат от KIE)
        filename = f"{uuid.uuid4().hex}.png"
        filepath = STORAGE_DIR / filename
        filepath.write_bytes(image_bytes)

        # Формирование URL для доступа к изображению
        base_url = os.getenv('IMAGE_SERVICE_PUBLIC_BASE_URL', str(request.base_url)).rstrip("/")
        image_url = f"{base_url}/images/{filename}"

        logger.info(f"Изображение успешно сгенерировано: {image_url}")

        return GenerateImageResponse(
            image_url=image_url,
            model_used="kie-nano-banana",
            success=True,
            message="Изображение успешно сгенерировано через KIE AI"
        )

    except HTTPException:
        raise
    except ValueError as e:
        # Ошибки валидации (Invalid API key, Insufficient credits, и т.д.)
        error_msg = f"Ошибка конфигурации KIE API: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=503, detail=error_msg)
    except TimeoutError as e:
        error_msg = f"Таймаут при генерации изображения: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
    except Exception as e:
        error_msg = f"Ошибка генерации изображения: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/status")
async def get_generation_status():
    """Получить статус сервиса генерации изображений"""
    return {
        "provider": "kie-nano-banana",
        "model": "google/nano-banana (Gemini 2.5 Flash)",
        "api_key_configured": bool(settings.KIE_API_KEY),
        "api_base_url": settings.KIE_API_BASE_URL,
        "timeout": settings.KIE_TIMEOUT,
        "storage_path": str(STORAGE_DIR),
        "storage_exists": STORAGE_DIR.exists(),
        "cost_per_image": "$0.02 USD"
    }


@router.post("/upload", response_model=GenerateImageResponse)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Загрузка пользовательского изображения

    Принимает изображение от пользователя, сохраняет в storage и возвращает URL
    """
    try:
        # Проверка типа файла
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"Недопустимый тип файла: {file.content_type}. Разрешены только изображения."
            )

        # Проверка размера файла (макс 10MB)
        max_size = 10 * 1024 * 1024  # 10 MB
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"Размер файла ({file_size} байт) превышает максимально допустимый ({max_size} байт)"
            )

        # Определяем расширение файла
        extension_map = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp'
        }
        file_extension = extension_map.get(file.content_type, 'jpg')

        # Генерируем уникальное имя файла
        filename = f"{uuid.uuid4().hex}.{file_extension}"
        filepath = STORAGE_DIR / filename

        # Сохраняем файл
        filepath.write_bytes(file_content)

        # Формируем URL для доступа к изображению
        base_url = os.getenv('IMAGE_SERVICE_PUBLIC_BASE_URL', str(request.base_url)).rstrip("/")
        image_url = f"{base_url}/images/{filename}"

        username = current_user.username if current_user else 'anonymous'
        logger.info(f"Пользователь {username} загрузил изображение: {filename} ({file_size} байт)")

        return GenerateImageResponse(
            image_url=image_url,
            model_used="user-upload",
            success=True,
            message="Изображение успешно загружено"
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Ошибка загрузки изображения: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
