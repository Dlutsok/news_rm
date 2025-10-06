from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class PlatformType(str, Enum):
    GS = "GS"  # gynecology.school
    PS = "PS"  # pediatrics.school  
    TS = "TS"  # therapy.school

class NewsSource(BaseModel):
    title: str
    url: HttpUrl
    content: str
    published_date: Optional[datetime] = None
    published_time: Optional[str] = None  # Время публикации (например, "18:19")
    views_count: Optional[int] = None     # Количество просмотров
    author: Optional[str] = None
    tags: List[str] = []
    source_site: str = "medvestnik.ru"

class AdaptedNews(BaseModel):
    original_news: NewsSource
    platform: PlatformType
    adapted_title: str
    adapted_content: str
    seo_title: str
    seo_description: str
    seo_keywords: List[str]
    relevance_score: float
    adaptation_notes: Optional[str] = None

class ParseRequest(BaseModel):
    sources: Optional[List[str]] = None  # Список источников для парсинга
    max_articles: int = 10
    date_filter: Optional[str] = None  # "today", "week", "month" или "YYYY-MM-DD"
    fetch_full_content: bool = True  # Загружать ли полный контент статей
    combine_results: bool = False  # Объединить результаты из всех источников

class MultiSourceParseRequest(BaseModel):
    sources: List[str]  # Обязательный список источников
    max_articles_per_source: int = 10
    date_filter: Optional[str] = None
    fetch_full_content: bool = True

class SourceInfo(BaseModel):
    name: str
    base_url: str
    status: str  # 'active' или 'inactive'

class MultiSourceResponse(BaseModel):
    status: str
    total_articles: int
    sources: Dict[str, List[NewsSource]]  # Результаты по источникам
    parsed_at: datetime

class CombinedNewsResponse(BaseModel):
    status: str
    total_articles: int
    articles: List[NewsSource]  # Объединенный список статей
    parsed_at: datetime

class AdaptationRequest(BaseModel):
    news_id: str
    platform: PlatformType
    custom_prompt: Optional[str] = None

class PublishRequest(BaseModel):
    adapted_news_id: str
    platform: PlatformType
    section: str = "/news/"
    schedule_time: Optional[datetime] = None

class NewsListResponse(BaseModel):
    news: List[NewsSource]
    total_count: int
    parsed_at: datetime

class AdaptationResponse(BaseModel):
    adapted_news: AdaptedNews
    processing_time: float
    success: bool
    error_message: Optional[str] = None

# Новые модели для генерации новостей
class ProjectType(str, Enum):
    GYNECOLOGY = "gynecology.school"
    THERAPY = "therapy.school"
    PEDIATRICS = "pediatrics.school"

class ArticleSummaryRequest(BaseModel):
    article_id: int
    project: ProjectType

class ArticleSummary(BaseModel):
    summary: str
    facts: List[str]

class SummaryConfirmationRequest(BaseModel):
    article_id: int
    project: ProjectType
    summary: str
    facts: List[str]
    action: str  # "confirm", "regenerate", "edit"

class GeneratedArticle(BaseModel):
    news_text: str
    seo_title: str
    seo_description: str
    seo_keywords: List[str]
    image_prompt: str
    image_url: str

class ArticleGenerationRequest(BaseModel):
    article_id: int
    project: ProjectType
    summary: str
    facts: List[str]

class GeneratedArticleResponse(BaseModel):
    article_id: int
    project: ProjectType
    generated_article: GeneratedArticle
    draft_id: int
    success: bool
    error_message: Optional[str] = None

class ArticleDraft(BaseModel):
    id: int
    article_id: int
    project: ProjectType
    summary: str
    facts: List[str]
    generated_content: Optional[GeneratedArticle] = None
    status: str  # "summary_pending", "confirmed", "generated", "published"
    created_at: datetime
    updated_at: datetime

class ArticleDraftUpdate(BaseModel):
    """Модель для обновления содержимого черновика"""
    news_text: str
    seo_title: str
    seo_description: str
    seo_keywords: List[str]
    image_prompt: Optional[str] = None
    image_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None

class RegenerateImageRequest(BaseModel):
    draft_id: int
    new_prompt: Optional[str] = None

class PublishToBitrixRequest(BaseModel):
    """Модель для публикации статьи в Bitrix CMS"""
    draft_id: int
    project_code: str  # Код проекта (GS, TS, PS)
    main_type: Optional[int] = None  # ID главной нозологии


# Схемы для настроек Bitrix проектов
class BitrixProjectSettingsBase(BaseModel):
    """Базовая модель настроек проекта Bitrix"""
    project_code: str
    project_name: str
    display_name: str
    api_url: Optional[str] = None
    api_token: Optional[str] = None
    iblock_id: Optional[int] = 38
    is_active: bool = True
    description: Optional[str] = None


class BitrixProjectSettingsCreate(BitrixProjectSettingsBase):
    """Модель для создания настроек проекта"""
    pass


class BitrixProjectSettingsUpdate(BaseModel):
    """Модель для обновления настроек проекта"""
    project_name: Optional[str] = None
    display_name: Optional[str] = None
    api_url: Optional[str] = None
    api_token: Optional[str] = None
    iblock_id: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class BitrixProjectSettingsRead(BitrixProjectSettingsBase):
    """Модель для чтения настроек проекта"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Схемы для общих настроек приложения
class AppSettingsBase(BaseModel):
    """Базовая модель настроек приложения"""
    setting_key: str
    setting_value: Optional[str] = None
    setting_type: str = "string"
    description: Optional[str] = None
    category: str = "general"


class AppSettingsCreate(AppSettingsBase):
    """Модель для создания настройки"""
    pass


class AppSettingsUpdate(BaseModel):
    """Модель для обновления настройки"""
    setting_value: Optional[str] = None
    setting_type: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class AppSettingsRead(AppSettingsBase):
    """Модель для чтения настройки"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Модель для получения всех настроек
class SettingsResponse(BaseModel):
    """Ответ с настройками"""
    bitrix_projects: List[BitrixProjectSettingsRead]
    app_settings: List[AppSettingsRead]


# Модели для отложенной публикации
class PublicationMode(str, Enum):
    """Режимы публикации"""
    NOW = "now"
    LATER = "later"


class PublishRequest(BaseModel):
    """Запрос на публикацию новости"""
    draft_id: int
    project_code: str  # GS, TS, PS
    mode: PublicationMode
    scheduled_at: Optional[datetime] = None  # Обязательно для mode="later"
    main_type: Optional[int] = None


class ScheduleRequest(BaseModel):
    """Запрос на изменение времени отложенной публикации"""
    draft_id: int
    scheduled_at: datetime


class PublishedNewsFilter(BaseModel):
    """Фильтры для списка опубликованных новостей"""
    project: Optional[str] = None
    status: Optional[str] = None  # scheduled, published
    author: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    limit: int = 20


class PublishedNewsItem(BaseModel):
    """Элемент списка опубликованных новостей"""
    id: int
    article_id: int
    project: str
    project_name: str
    title: str
    seo_title: Optional[str] = None
    news_text: Optional[str] = None
    image_url: Optional[str] = None
    generated_image_url: Optional[str] = None
    author_name: str
    status: str
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    bitrix_id: Optional[int] = None


class PublishedNewsResponse(BaseModel):
    """Ответ со списком опубликованных новостей"""
    items: List[PublishedNewsItem]
    total: int
    page: int
    pages: int