import os
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import pathlib

# Загружаем .env файл из корня проекта
env_path = pathlib.Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    """Конфигурация приложения"""

    # Базовые пути
    BASE_DIR: Path = Path(__file__).parent.parent.absolute()

    # API настройки
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Medical News Automation"
    VERSION: str = "1.0.0"
    
    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Прокси для OpenAI (для обхода блокировок РФ)
    OPENAI_PROXY_URL: str = os.getenv("OPENAI_PROXY_URL", "")

    # KIE AI Configuration (Nano Banana - Google Gemini 2.5 Flash для генерации изображений)
    KIE_API_KEY: str = os.getenv("KIE_API_KEY", "")
    KIE_API_BASE_URL: str = os.getenv("KIE_API_BASE_URL", "https://api.kie.ai/api/v1")
    KIE_TIMEOUT: int = int(os.getenv("KIE_TIMEOUT", "300"))  # Timeout в секундах (5 минут)

    # База данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/news_aggregator")
    
    # Внешние источники
    MEDVESTNIK_BASE_URL: str = "https://medvestnik.ru"
    MEDVESTNIK_NEWS_URL: str = "https://medvestnik.ru/content/roubric/news"
    
    # Источники новостей
    NEWS_SOURCES: Dict[str, Dict[str, Any]] = {
        "medvestnik": {
            "name": "Медвестник",
            "url": "https://medvestnik.ru/content/roubric/news",
            "topics": ["медицинские новости", "исследования", "здравоохранение"],
            "style": "информационный"
        },
        "ria": {
            "name": "РИА Новости",
            "url": "https://ria.ru",
            "topics": ["общие новости", "медицина", "наука"],
            "style": "информационный"
        }
    }
    
    # Целевые платформы для адаптации
    PLATFORMS: Dict[str, Dict[str, Any]] = {
        "GS": {
            "name": "Gynecology School",
            "topics": ["гинекология", "женское здоровье", "гормоны", "ВРТ", "УЗИ"],
            "style": "образовательный",
            "target_audience": "врачи-гинекологи",
            "max_length": 2000
        },
        "PS": {
            "name": "Pediatrics School", 
            "topics": ["педиатрия", "вакцинация", "питание", "неврология"],
            "style": "образовательный",
            "target_audience": "педиатры",
            "max_length": 2000
        },
        "TS": {
            "name": "Therapy School",
            "topics": ["терапия", "кардиология", "эндокринология", "диагностика"],
            "style": "образовательный", 
            "target_audience": "врачи-терапевты",
            "max_length": 2000
        }
    }
    
    # Логирование
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Bitrix CMS API для разных проектов
    BITRIX_PROJECTS: Dict[str, Dict[str, Any]] = {
        "GS": {  # Gynecology School
            "name": "gynecology.school",
            "display_name": "Гинекология и акушерство",
            "api_url": os.getenv("BITRIX_GS_API_URL", "http://94.241.140.236/api/ai_news_import.php"),
            "api_token": os.getenv("BITRIX_GS_API_TOKEN", ""),
            "iblock_id": int(os.getenv("BITRIX_GS_IBLOCK_ID", "38"))
        },
        "TS": {  # Therapy School
            "name": "therapy.school",
            "display_name": "Терапия и общая медицина",
            "api_url": os.getenv("BITRIX_TS_API_URL", ""),
            "api_token": os.getenv("BITRIX_TS_API_TOKEN", ""),
            "iblock_id": int(os.getenv("BITRIX_TS_IBLOCK_ID", "38"))
        },
        "PS": {  # Pediatrics School
            "name": "pediatrics.school", 
            "display_name": "Педиатрия и детская медицина",
            "api_url": os.getenv("BITRIX_PS_API_URL", ""),
            "api_token": os.getenv("BITRIX_PS_API_TOKEN", ""),
            "iblock_id": int(os.getenv("BITRIX_PS_IBLOCK_ID", "38"))
        }
    }
    
    # Обратная совместимость - старые настройки Bitrix (по умолчанию для GS)
    BITRIX_API_URL: str = os.getenv("BITRIX_API_URL", "http://94.241.140.236/api/ai_news_import.php")
    BITRIX_API_TOKEN: str = os.getenv("BITRIX_API_TOKEN", "")
    BITRIX_IBLOCK_ID: int = int(os.getenv("BITRIX_IBLOCK_ID", "38"))
    
    # JWT и авторизация
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 12
    
    # Данные начального администратора
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # Разработка
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS настройки
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Получить список разрешенных CORS origins в зависимости от режима"""
        if self.DEBUG:
            # В режиме разработки - разрешаем localhost и продакшен
            origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        else:
            # В продакшене - только продакшен домены
            origins_str = os.getenv("CORS_ORIGINS_PRODUCTION", "https://admin.news.rusmedical.ru")
        
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Image generation service URL (for backward compatibility)
    IMAGE_SERVICE_URL: str = os.getenv("IMAGE_SERVICE_URL", "http://localhost:8000")

    # Rate Limiting настройки
    RATE_LIMITING_ENABLED: bool = os.getenv("RATE_LIMITING_ENABLED", "true").lower() == "true"
    
    # Основные лимиты (запросы в минуту)
    RATE_LIMIT_AUTH: int = int(os.getenv("RATE_LIMIT_AUTH", "20"))
    RATE_LIMIT_PARSING: int = int(os.getenv("RATE_LIMIT_PARSING", "5"))
    RATE_LIMIT_GENERATION: int = int(os.getenv("RATE_LIMIT_GENERATION", "10"))
    RATE_LIMIT_ADMIN: int = int(os.getenv("RATE_LIMIT_ADMIN", "30"))
    RATE_LIMIT_DEFAULT: int = int(os.getenv("RATE_LIMIT_DEFAULT", "100"))

# Создаем экземпляр настроек
settings = Settings()