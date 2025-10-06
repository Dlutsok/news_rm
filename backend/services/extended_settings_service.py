"""
Расширенный сервис настроек с полным списком всех возможных параметров приложения
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from database.connection import DatabaseSession
from database.models import AppSettings
from models.schemas import AppSettingsCreate
import logging

logger = logging.getLogger(__name__)

class ExtendedSettingsService:
    """Расширенный сервис для управления всеми настройками приложения"""
    
    def __init__(self):
        self.session = DatabaseSession
    
    def initialize_all_settings(self):
        """Инициализация всех возможных настроек приложения"""
        try:
            # Все возможные настройки приложения
            all_settings = [
                # OpenAI настройки
                AppSettingsCreate(
                    setting_key="openai_api_key",
                    setting_value="",
                    setting_type="string",
                    description="API ключ для OpenAI",
                    category="openai"
                ),
                AppSettingsCreate(
                    setting_key="openai_model",
                    setting_value="gpt-4",
                    setting_type="string",
                    description="Модель OpenAI для генерации",
                    category="openai"
                ),
                AppSettingsCreate(
                    setting_key="openai_summary_model",
                    setting_value="gpt-4o",
                    setting_type="string",
                    description="Модель OpenAI для создания выжимок (переключено на GPT-4o для качества)",
                    category="openai"
                ),
                AppSettingsCreate(
                    setting_key="openai_generation_model",
                    setting_value="gpt-4o",
                    setting_type="string",
                    description="Модель OpenAI для генерации полных статей",
                    category="openai"
                ),
                AppSettingsCreate(
                    setting_key="openai_temperature",
                    setting_value="0.6",
                    setting_type="float",
                    description="Температура для генерации текста (0.0-1.0)",
                    category="openai"
                ),
                AppSettingsCreate(
                    setting_key="openai_max_tokens",
                    setting_value="8000",
                    setting_type="int",
                    description="Максимальное количество токенов для генерации (увеличено для длинных статей)",
                    category="openai"
                ),
                
                # Парсинг настройки
                AppSettingsCreate(
                    setting_key="news_parsing_limit",
                    setting_value="100",
                    setting_type="int",
                    description="Лимит новостей для парсинга за раз",
                    category="parsing"
                ),
                AppSettingsCreate(
                    setting_key="parsing_days_back",
                    setting_value="7",
                    setting_type="int",
                    description="Количество дней назад для парсинга новостей",
                    category="parsing"
                ),
                AppSettingsCreate(
                    setting_key="article_content_limit",
                    setting_value="6000",
                    setting_type="int",
                    description="Максимальная длина контента статьи в символах",
                    category="parsing"
                ),
                AppSettingsCreate(
                    setting_key="article_min_paragraph_length",
                    setting_value="20",
                    setting_type="int",
                    description="Минимальная длина параграфа для включения в статью",
                    category="parsing"
                ),
                AppSettingsCreate(
                    setting_key="parsing_timeout_seconds",
                    setting_value="30",
                    setting_type="int",
                    description="Таймаут для парсинга одной статьи в секундах",
                    category="parsing"
                ),
                AppSettingsCreate(
                    setting_key="parsing_max_retries",
                    setting_value="3",
                    setting_type="int",
                    description="Максимальное количество попыток парсинга статьи",
                    category="parsing"
                ),
                
                # Публикация настройки
                AppSettingsCreate(
                    setting_key="auto_publish_enabled",
                    setting_value="false",
                    setting_type="bool",
                    description="Автоматическая публикация статей",
                    category="publishing"
                ),
                AppSettingsCreate(
                    setting_key="publish_delay_minutes",
                    setting_value="30",
                    setting_type="int",
                    description="Задержка между публикациями в минутах",
                    category="publishing"
                ),
                AppSettingsCreate(
                    setting_key="max_daily_publications",
                    setting_value="10",
                    setting_type="int",
                    description="Максимальное количество публикаций в день",
                    category="publishing"
                ),
                
                # Генерация контента
                AppSettingsCreate(
                    setting_key="article_min_length",
                    setting_value="2500",
                    setting_type="int",
                    description="Минимальная длина генерируемой статьи в символах",
                    category="generation"
                ),
                AppSettingsCreate(
                    setting_key="article_max_length",
                    setting_value="4000",
                    setting_type="int",
                    description="Максимальная длина генерируемой статьи в символах",
                    category="generation"
                ),
                AppSettingsCreate(
                    setting_key="summary_max_length",
                    setting_value="1200",
                    setting_type="int",
                    description="Максимальная длина выжимки статьи в символах",
                    category="generation"
                ),
                AppSettingsCreate(
                    setting_key="seo_title_max_length",
                    setting_value="60",
                    setting_type="int",
                    description="Максимальная длина SEO заголовка",
                    category="generation"
                ),
                AppSettingsCreate(
                    setting_key="seo_description_max_length",
                    setting_value="160",
                    setting_type="int",
                    description="Максимальная длина SEO описания",
                    category="generation"
                ),
                AppSettingsCreate(
                    setting_key="keywords_count",
                    setting_value="7",
                    setting_type="int",
                    description="Количество SEO ключевых слов",
                    category="generation"
                ),
                
                # Системные настройки
                AppSettingsCreate(
                    setting_key="log_level",
                    setting_value="INFO",
                    setting_type="string",
                    description="Уровень логирования (DEBUG, INFO, WARNING, ERROR)",
                    category="system"
                ),
                AppSettingsCreate(
                    setting_key="debug_mode",
                    setting_value="false",
                    setting_type="bool",
                    description="Режим отладки",
                    category="system"
                ),
                AppSettingsCreate(
                    setting_key="request_timeout",
                    setting_value="30",
                    setting_type="int",
                    description="Таймаут HTTP запросов в секундах",
                    category="system"
                ),
                AppSettingsCreate(
                    setting_key="max_concurrent_requests",
                    setting_value="10",
                    setting_type="int",
                    description="Максимальное количество одновременных запросов",
                    category="system"
                ),
                
                # Источники новостей
                AppSettingsCreate(
                    setting_key="medvestnik_enabled",
                    setting_value="true",
                    setting_type="bool",
                    description="Включить парсинг Медвестника",
                    category="sources"
                ),
                AppSettingsCreate(
                    setting_key="ria_enabled",
                    setting_value="true",
                    setting_type="bool",
                    description="Включить парсинг РИА Новости",
                    category="sources"
                ),
                AppSettingsCreate(
                    setting_key="remedium_enabled",
                    setting_value="true",
                    setting_type="bool",
                    description="Включить парсинг Remedium",
                    category="sources"
                ),
                AppSettingsCreate(
                    setting_key="rbc_enabled",
                    setting_value="true",
                    setting_type="bool",
                    description="Включить парсинг РБК",
                    category="sources"
                ),
                AppSettingsCreate(
                    setting_key="aig_enabled",
                    setting_value="true",
                    setting_type="bool",
                    description="Включить парсинг AiG",
                    category="sources"
                ),
                
                # Фильтрация контента
                AppSettingsCreate(
                    setting_key="content_quality_threshold",
                    setting_value="0.7",
                    setting_type="float",
                    description="Порог качества контента (0.0-1.0)",
                    category="filtering"
                ),
                AppSettingsCreate(
                    setting_key="relevance_threshold",
                    setting_value="1",
                    setting_type="int",
                    description="Минимальный балл релевантности для платформы",
                    category="filtering"
                ),
                AppSettingsCreate(
                    setting_key="duplicate_detection_enabled",
                    setting_value="true",
                    setting_type="bool",
                    description="Включить обнаружение дубликатов",
                    category="filtering"
                ),
                
                # Мониторинг и метрики
                AppSettingsCreate(
                    setting_key="metrics_enabled",
                    setting_value="true",
                    setting_type="bool",
                    description="Включить сбор метрик",
                    category="monitoring"
                ),
                AppSettingsCreate(
                    setting_key="health_check_interval",
                    setting_value="300",
                    setting_type="int",
                    description="Интервал проверки здоровья системы в секундах",
                    category="monitoring"
                ),
                AppSettingsCreate(
                    setting_key="stats_retention_days",
                    setting_value="30",
                    setting_type="int",
                    description="Количество дней хранения статистики",
                    category="monitoring"
                ),
                
                # Интеграции
                AppSettingsCreate(
                    setting_key="bitrix_connection_timeout",
                    setting_value="30",
                    setting_type="int",
                    description="Таймаут подключения к Bitrix в секундах",
                    category="integrations"
                ),
                AppSettingsCreate(
                    setting_key="bitrix_retry_attempts",
                    setting_value="3",
                    setting_type="int",
                    description="Количество попыток подключения к Bitrix",
                    category="integrations"
                ),
                
                # Кэширование
                AppSettingsCreate(
                    setting_key="cache_enabled",
                    setting_value="true",
                    setting_type="bool",
                    description="Включить кэширование",
                    category="cache"
                ),
                AppSettingsCreate(
                    setting_key="cache_ttl_minutes",
                    setting_value="60",
                    setting_type="int",
                    description="Время жизни кэша в минутах",
                    category="cache"
                ),
                
                # Безопасность
                AppSettingsCreate(
                    setting_key="rate_limit_requests_per_minute",
                    setting_value="100",
                    setting_type="int",
                    description="Лимит запросов в минуту",
                    category="security"
                ),
                AppSettingsCreate(
                    setting_key="api_key_required",
                    setting_value="false",
                    setting_type="bool",
                    description="Требовать API ключ для доступа",
                    category="security"
                )
            ]
            
            # Создаем настройки, которых еще нет
            with self.session() as session:
                for setting_data in all_settings:
                    stmt = select(AppSettings).where(AppSettings.setting_key == setting_data.setting_key)
                    existing = session.exec(stmt).first()
                    if not existing:
                        setting = AppSettings(**setting_data.dict())
                        session.add(setting)
                        logger.info(f"Created setting: {setting_data.setting_key}")
                
                session.commit()
            
            logger.info("Initialized all extended app settings")
            
        except Exception as e:
            logger.error(f"Error initializing extended settings: {e}")
    
    def get_settings_by_categories(self) -> Dict[str, List[Dict]]:
        """Получить все настройки, сгруппированные по категориям"""
        try:
            with self.session() as session:
                stmt = select(AppSettings).order_by(AppSettings.category, AppSettings.setting_key)
                settings = session.exec(stmt).all()
                
                categories = {}
                for setting in settings:
                    if setting.category not in categories:
                        categories[setting.category] = []
                    
                    categories[setting.category].append({
                        "id": setting.id,
                        "setting_key": setting.setting_key,
                        "setting_value": setting.setting_value,
                        "setting_type": setting.setting_type,
                        "description": setting.description,
                        "category": setting.category,
                        "created_at": setting.created_at,
                        "updated_at": setting.updated_at
                    })
                
                return categories
                
        except Exception as e:
            logger.error(f"Error getting settings by categories: {e}")
            return {}
    
    def get_default_system_settings(self) -> Dict[str, Dict[str, str]]:
        """Получить системные настройки по умолчанию для инициализации"""
        return {
            # Системные параметры
            "log_level": {
                "default_value": "INFO",
                "type": "string",
                "description": "Уровень логирования (DEBUG, INFO, WARNING, ERROR)"
            },
            "debug_mode": {
                "default_value": "false",
                "type": "bool",
                "description": "Режим отладки"
            },
            "request_timeout": {
                "default_value": "30",
                "type": "int",
                "description": "Таймаут HTTP запросов в секундах"
            },
            "max_concurrent_requests": {
                "default_value": "10",
                "type": "int",
                "description": "Максимальное количество одновременных запросов"
            },
            
            # Парсинг новостей
            "news_parsing_limit": {
                "default_value": "100",
                "type": "int",
                "description": "Лимит новостей для парсинга за раз"
            },
            "parsing_days_back": {
                "default_value": "7",
                "type": "int",
                "description": "Количество дней назад для парсинга новостей"
            },
            "parsing_timeout_seconds": {
                "default_value": "30",
                "type": "int",
                "description": "Таймаут для парсинга одной статьи в секундах"
            },
            "article_content_limit": {
                "default_value": "6000",
                "type": "int",
                "description": "Максимальная длина контента статьи в символах"
            },
            "article_min_paragraph_length": {
                "default_value": "20",
                "type": "int",
                "description": "Минимальная длина параграфа для включения в статью"
            },
            "parsing_max_retries": {
                "default_value": "3",
                "type": "int",
                "description": "Максимальное количество попыток парсинга статьи"
            },
            
            # Публикация
            "auto_publish_enabled": {
                "default_value": "false",
                "type": "bool",
                "description": "Автоматическая публикация статей"
            },
            "max_daily_publications": {
                "default_value": "10",
                "type": "int",
                "description": "Максимальное количество публикаций в день"
            },
            "publish_delay_minutes": {
                "default_value": "30",
                "type": "int",
                "description": "Задержка между публикациями в минутах"
            },
            
            # Генерация контента
            "article_min_length": {
                "default_value": "2000",
                "type": "int",
                "description": "Минимальная длина генерируемой статьи в символах"
            },
            "article_max_length": {
                "default_value": "4000",
                "type": "int",
                "description": "Максимальная длина генерируемой статьи в символах"
            },
            "summary_max_length": {
                "default_value": "1200",
                "type": "int",
                "description": "Максимальная длина выжимки статьи в символах"
            },
            "seo_title_max_length": {
                "default_value": "60",
                "type": "int",
                "description": "Максимальная длина SEO заголовка"
            },
            "seo_description_max_length": {
                "default_value": "160",
                "type": "int",
                "description": "Максимальная длина SEO описания"
            },
            "keywords_count": {
                "default_value": "7",
                "type": "int",
                "description": "Количество SEO ключевых слов"
            },
            
            # Источники новостей
            "medvestnik_enabled": {
                "default_value": "true",
                "type": "bool",
                "description": "Включить парсинг Медвестника"
            },
            "ria_enabled": {
                "default_value": "true",
                "type": "bool",
                "description": "Включить парсинг РИА Новости"
            },
            "remedium_enabled": {
                "default_value": "true",
                "type": "bool",
                "description": "Включить парсинг Remedium"
            },
            "rbc_enabled": {
                "default_value": "true",
                "type": "bool",
                "description": "Включить парсинг РБК"
            },
            "aig_enabled": {
                "default_value": "true",
                "type": "bool",
                "description": "Включить парсинг AiG"
            },
            
            # Фильтрация контента
            "content_quality_threshold": {
                "default_value": "0.7",
                "type": "float",
                "description": "Порог качества контента (0.0-1.0)"
            },
            "relevance_threshold": {
                "default_value": "1",
                "type": "int",
                "description": "Минимальный балл релевантности для платформы"
            },
            "duplicate_detection_enabled": {
                "default_value": "true",
                "type": "bool",
                "description": "Включить обнаружение дубликатов"
            },
            
            # Мониторинг и метрики
            "metrics_enabled": {
                "default_value": "true",
                "type": "bool",
                "description": "Включить сбор метрик"
            },
            "health_check_interval": {
                "default_value": "300",
                "type": "int",
                "description": "Интервал проверки здоровья системы в секундах"
            },
            "stats_retention_days": {
                "default_value": "30",
                "type": "int",
                "description": "Количество дней хранения статистики"
            },
            
            # Интеграции
            "bitrix_connection_timeout": {
                "default_value": "30",
                "type": "int",
                "description": "Таймаут подключения к Bitrix в секундах"
            },
            "bitrix_retry_attempts": {
                "default_value": "3",
                "type": "int",
                "description": "Количество попыток подключения к Bitrix"
            },
            
            # Кэширование
            "cache_enabled": {
                "default_value": "true",
                "type": "bool",
                "description": "Включить кэширование"
            },
            "cache_ttl_minutes": {
                "default_value": "60",
                "type": "int",
                "description": "Время жизни кэша в минутах"
            },
            
            # Безопасность
            "rate_limit_requests_per_minute": {
                "default_value": "100",
                "type": "int",
                "description": "Лимит запросов в минуту"
            },
            "api_key_required": {
                "default_value": "false",
                "type": "bool",
                "description": "Требовать API ключ для доступа"
            }
        }

# Создаем экземпляр сервиса
extended_settings_service = ExtendedSettingsService()