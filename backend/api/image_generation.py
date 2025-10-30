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
    """
    Очистка промпта от нежелательных слов, которые могут привести к нереалистичным изображениям.
    Удаляются стилистические термины, указывающие на иллюстрации, мультипликацию, CGI и т.д.
    """
    banned = [
        # Иллюстрация и графика
        "иллюстрация",
        "иллюстративный",
        "рисунок",
        "нарисованный",
        "графика",
        "схема",
        "схематичный",
        "диаграмма",
        # Мультипликация и анимация
        "мультяш",
        "мультик",
        "cartoon",
        "анимация",
        "аниме",
        "комикс",
        "manga",
        # Векторная и плоская графика
        "vector",
        "flat",
        "flat design",
        "векторный",
        # 3D и CGI
        "3d",
        "3D",
        "cgi",
        "CGI",
        "рендер",
        "render",
        "rendered",
        "low poly",
        "полигональный",
        # Стили, которые не подходят для реализма
        "pixar",
        "disney",
        "dreamworks",
        "абстракт",
        "abstract",
        "сюрреализм",
        "surreal",
        "фантазия",
        "fantasy",
        "sci-fi",
        "научная фантастика",
    ]
    cleaned = raw or ""
    for token in banned:
        # Используем case-insensitive замену
        cleaned = cleaned.replace(token.lower(), "")
        cleaned = cleaned.replace(token.capitalize(), "")
        cleaned = cleaned.replace(token.upper(), "")
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

        # Улучшенный enhanced_prompt для медицинских изображений
        # Менее перегруженный, более сфокусированный на реализме и медицинском контексте
        enhanced_prompt = (
            f"Фотореалистичное медицинское изображение: {prompt_ru}. "
            "Профессиональная фотография, реалистичное освещение, естественные цвета и текстуры. "
            "Четкие детали, реальные объекты, документальный стиль медицинской фотографии. "
            "High-quality medical photography, realistic materials, natural lighting, authentic textures."
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