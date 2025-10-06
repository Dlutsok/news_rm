import os
import uuid
from pathlib import Path
from typing import Optional
import logging

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.config import settings
from api.dependencies import get_current_user_optional
from database.models import User

logger = logging.getLogger(__name__)

router = APIRouter()

try:
    from yandex_cloud_ml_sdk import YCloudML
except ImportError as e:
    YCloudML = None
    logger.warning(f"yandex-cloud-ml-sdk не установлен: {e}")


class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., description="Текстовый промпт для генерации изображения")
    width_ratio: Optional[int] = Field(1, description="Отношение ширины (1-2)")
    height_ratio: Optional[int] = Field(1, description="Отношение высоты (1-2)")
    seed: Optional[int] = Field(None, description="Сид для детерминированности")


class GenerateImageResponse(BaseModel):
    image_url: str
    model_used: str = "yandex-art"
    success: bool = True
    message: str = "Изображение успешно сгенерировано"


# Настройки для хранения изображений
STORAGE_DIR = Path(settings.BASE_DIR) / "storage" / "images"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Yandex Cloud настройки
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID", "")
YC_API_KEY = os.getenv("YC_API_KEY", "")


def sanitize_prompt(raw: str) -> str:
    """Очистка промпта от нежелательных слов (только стилистические термины)"""
    banned = [
        "иллюстрация",
        "иллюстративный",
        "рисунок",
        "мультяш",
        "cartoon",
        "vector",
        "flat",
        "аниме",
        "анимация",
        "комикс",
        "3d",
        "3D",
        "cgi",
        "CGI",
        "рендер",
        "render",
        "low poly",
        "pixar",
    ]
    cleaned = raw or ""
    for token in banned:
        cleaned = cleaned.replace(token, "")
    return cleaned.strip()


@router.get("/health")
async def image_service_health():
    """Проверка здоровья сервиса генерации изображений"""
    return {
        "status": "healthy",
        "service": "image-generation",
        "yandex_cloud_available": YCloudML is not None and bool(YC_FOLDER_ID and YC_API_KEY)
    }


@router.post("/generate", response_model=GenerateImageResponse)
async def generate_image(
    request: Request,
    body: GenerateImageRequest,
    current_user: User = Depends(get_current_user_optional)
):
    """Генерация изображения с помощью YandexART"""
    try:
        # Проверяем доступность сервиса
        if YCloudML is None:
            raise HTTPException(
                status_code=503,
                detail="yandex-cloud-ml-sdk не установлен"
            )

        if not YC_FOLDER_ID or not YC_API_KEY:
            raise HTTPException(
                status_code=503,
                detail="YC_FOLDER_ID или YC_API_KEY не настроены"
            )

        # Инициализация SDK
        sdk = YCloudML(folder_id=YC_FOLDER_ID, auth=YC_API_KEY)
        model = sdk.models.image_generation("yandex-art")

        # Настройка соотношения сторон
        width_ratio = body.width_ratio if body.width_ratio in (1, 2) else 1
        height_ratio = body.height_ratio if body.height_ratio in (1, 2) else 1
        model = model.configure(
            width_ratio=width_ratio,
            height_ratio=height_ratio,
            seed=body.seed
        )

        # Подготовка промпта
        prompt_ru = sanitize_prompt(body.prompt)
        enhanced_prompt = (
            f"Фотореалистичная фотография: {prompt_ru}. "
            "Снято камерой Canon EOS или Nikon, естественное дневное освещение, "
            "реальная земная обстановка, подлинные материалы и текстуры. "
            "Документальный стиль, как в National Geographic, реальные физические объекты, "
            "обычная земная среда, достоверные пропорции и перспектива. "
            "Photo taken on Earth, realistic lighting and shadows, authentic human environments, "
            "natural physics, real-world materials, documentary photography style."
        )

        logger.info(f"Генерируем изображение для пользователя {current_user.username if current_user else 'anonymous'}: {prompt_ru[:100]}...")

        # Генерация изображения
        operation = model.run_deferred(enhanced_prompt)
        result = operation.wait()

        image_bytes = result.image_bytes
        if not image_bytes:
            raise RuntimeError("Пустой ответ от модели YandexART")

        # Сохранение файла
        filename = f"{uuid.uuid4().hex}.jpeg"
        filepath = STORAGE_DIR / filename
        filepath.write_bytes(image_bytes)

        # Формирование URL для доступа к изображению
        base_url = os.getenv('IMAGE_SERVICE_PUBLIC_BASE_URL', str(request.base_url)).rstrip("/")
        image_url = f"{base_url}/images/{filename}"

        logger.info(f"Изображение успешно сгенерировано: {image_url}")

        return GenerateImageResponse(image_url=image_url)

    except Exception as e:
        error_msg = f"Ошибка генерации изображения: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/status")
async def get_generation_status():
    """Получить статус сервиса генерации изображений"""
    return {
        "sdk_available": YCloudML is not None,
        "credentials_configured": bool(YC_FOLDER_ID and YC_API_KEY),
        "storage_path": str(STORAGE_DIR),
        "storage_exists": STORAGE_DIR.exists()
    }