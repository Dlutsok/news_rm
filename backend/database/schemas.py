"""
Pydantic схемы для API запросов и ответов
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class ProjectType(str, Enum):
    """Типы проектов для генерации новостей"""
    GYNECOLOGY = "gynecology.school"
    THERAPY = "therapy.school"
    PEDIATRICS = "pediatrics.school"


# Схемы для генерации новостей
class ArticleSummaryRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Запрос на создание выжимки статьи"""
    article_id: int = Field(..., description="ID статьи для обработки")
    project: ProjectType = Field(..., description="Тип проекта")


class ArticleSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Ответ с выжимкой статьи"""
    article_id: int = Field(..., description="ID статьи")
    project: ProjectType = Field(..., description="Тип проекта")
    summary: str = Field(..., description="Выжимка статьи")
    facts: List[str] = Field(..., description="Ключевые факты")
    draft_id: int = Field(..., description="ID созданного черновика")


class SummaryConfirmationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Запрос на подтверждение выжимки"""
    draft_id: int = Field(..., description="ID черновика")
    summary: Optional[str] = Field(None, description="Отредактированная выжимка")
    facts: Optional[List[str]] = Field(None, description="Отредактированные факты")


class ArticleFormattingStyle(str, Enum):
    """Стили форматирования статьи"""
    STRUCTURED = "structured"  # Структурированный (много заголовков)
    NARRATIVE = "narrative"    # Повествовательный (мало заголовков)
    MIXED = "mixed"           # Смешанный


class ArticleParagraphLength(str, Enum):
    """Длина абзацев"""
    SHORT = "short"    # 1-2 предложения
    MEDIUM = "medium"  # 3-4 предложения
    LONG = "long"      # 5+ предложений


class ArticleFormattingOptions(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Параметры форматирования статьи"""
    headings_count: int = Field(default=3, ge=0, le=6, description="Количество заголовков (0-6)")
    style: ArticleFormattingStyle = Field(default=ArticleFormattingStyle.STRUCTURED, description="Стиль написания")
    paragraph_length: ArticleParagraphLength = Field(default=ArticleParagraphLength.MEDIUM, description="Длина абзацев")
    sentences_per_paragraph: int = Field(default=3, ge=1, le=5, description="Предложений в абзаце (1-5)")
    target_length: int = Field(default=3000, ge=2500, le=6000, description="Целевая длина статьи в символах")
    use_lists: bool = Field(default=True, description="Использовать списки")
    use_quotes: bool = Field(default=True, description="Использовать цитаты")


class ArticleGenerationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Запрос на генерацию полной статьи"""
    draft_id: int = Field(..., description="ID черновика")
    formatting_options: Optional[ArticleFormattingOptions] = Field(None, description="Параметры форматирования")


class GeneratedArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Ответ с сгенерированной статьей"""
    draft_id: int = Field(..., description="ID черновика")
    news_text: str = Field(..., description="Текст новости")
    seo_title: str = Field(..., description="SEO заголовок")
    seo_description: str = Field(..., description="SEO описание")
    seo_keywords: List[str] = Field(..., description="SEO ключевые слова")
    image_prompt: str = Field(..., description="Промпт для изображения")
    image_url: Optional[str] = Field(None, description="URL сгенерированного изображения")


class RegenerateImageRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Запрос на перегенерацию изображения"""
    draft_id: int = Field(..., description="ID черновика")
    new_prompt: Optional[str] = Field(None, description="Новый промпт для изображения")


class ArticleDraft(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Схема черновика статьи"""
    id: int = Field(..., description="ID черновика")
    article_id: int = Field(..., description="ID оригинальной статьи")
    project: ProjectType = Field(..., description="Тип проекта")
    summary: str = Field(..., description="Выжимка статьи")
    facts: List[str] = Field(..., description="Ключевые факты")
    news_text: Optional[str] = Field(None, description="Сгенерированный текст")
    seo_title: Optional[str] = Field(None, description="SEO заголовок")
    seo_description: Optional[str] = Field(None, description="SEO описание")
    seo_keywords: Optional[List[str]] = Field(None, description="SEO ключевые слова")
    image_prompt: Optional[str] = Field(None, description="Промпт для изображения")
    image_url: Optional[str] = Field(None, description="URL изображения")
    status: str = Field(..., description="Статус черновика")
    
    # Информация о публикации
    is_published: bool = Field(False, description="Опубликована ли статья")
    published_project_code: Optional[str] = Field(None, description="Код проекта публикации (GS, TS, PS)")
    published_project_name: Optional[str] = Field(None, description="Название проекта публикации")
    bitrix_id: Optional[int] = Field(None, description="ID в Bitrix CMS")
    published_at: Optional[datetime] = Field(None, description="Дата публикации")
    
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")


class NewsGenerationDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Схема для чтения черновика генерации новостей"""
    id: int
    article_id: int
    project: ProjectType
    summary: str
    facts: str  # JSON строка
    generated_news_text: Optional[str] = None
    generated_seo_title: Optional[str] = None
    generated_seo_description: Optional[str] = None
    generated_seo_keywords: Optional[str] = None  # JSON строка
    generated_image_prompt: Optional[str] = None
    generated_image_url: Optional[str] = None
    generated_tg_post: Optional[str] = None
    status: str

    # Поля для отслеживания ошибок
    last_error_message: Optional[str] = None
    last_error_step: Optional[str] = None
    last_error_at: Optional[datetime] = None
    can_retry: bool = True
    retry_count: int = 0

    # Информация о публикации
    is_published: bool = False
    published_project_code: Optional[str] = None
    published_project_name: Optional[str] = None
    bitrix_id: Optional[int] = None
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime


class GenerationLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Схема для чтения лога генерации"""
    id: int
    draft_id: int
    operation_type: str
    model_used: str
    success: bool
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    processing_time_seconds: Optional[float] = None
    created_at: datetime


# Дополнительные схемы
class SummarizeRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Запрос на создание выжимки статьи"""
    article_id: int = Field(..., description="ID статьи для обработки")
    project: ProjectType = Field(..., description="Тип проекта")


class SummarizeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Ответ с выжимкой статьи"""
    draft_id: int = Field(..., description="ID созданного черновика")
    summary: str = Field(..., description="Выжимка статьи")
    facts: List[str] = Field(..., description="Ключевые факты")
    status: str = Field(..., description="Статус черновика")


class ConfirmSummaryRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Запрос на подтверждение выжимки"""
    draft_id: int = Field(..., description="ID черновика")
    summary: Optional[str] = Field(None, description="Отредактированная выжимка")
    facts: Optional[List[str]] = Field(None, description="Отредактированные факты")


class GenerateArticleRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Запрос на генерацию полной статьи"""
    draft_id: int = Field(..., description="ID черновика")


class UpdateDraftRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Запрос на обновление черновика"""
    news_text: Optional[str] = Field(None, description="Обновленный текст новости")
    seo_title: Optional[str] = Field(None, description="Обновленный SEO заголовок")
    seo_description: Optional[str] = Field(None, description="Обновленное SEO описание")
    seo_keywords: Optional[List[str]] = Field(None, description="Обновленные SEO ключевые слова")
    image_prompt: Optional[str] = Field(None, description="Обновленный промпт для изображения")


class DraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Ответ с информацией о черновике"""
    id: int = Field(..., description="ID черновика")
    article_id: int = Field(..., description="ID оригинальной статьи")
    project: ProjectType = Field(..., description="Тип проекта")
    summary: str = Field(..., description="Выжимка статьи")
    facts: List[str] = Field(..., description="Ключевые факты")
    news_text: Optional[str] = Field(None, description="Сгенерированный текст")
    seo_title: Optional[str] = Field(None, description="SEO заголовок")
    seo_description: Optional[str] = Field(None, description="SEO описание")
    seo_keywords: Optional[List[str]] = Field(None, description="SEO ключевые слова")
    image_prompt: Optional[str] = Field(None, description="Промпт для изображения")
    image_url: Optional[str] = Field(None, description="URL изображения")
    status: str = Field(..., description="Статус черновика")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")


class DraftsListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Ответ со списком черновиков"""
    drafts: List[DraftResponse] = Field(..., description="Список черновиков")
    total: int = Field(..., description="Общее количество черновиков")
    page: int = Field(..., description="Текущая страница")
    per_page: int = Field(..., description="Количество на странице")


class GenerationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Ответ с логом генерации"""
    id: int = Field(..., description="ID лога")
    draft_id: int = Field(..., description="ID черновика")
    operation_type: str = Field(..., description="Тип операции")
    model_used: str = Field(..., description="Использованная модель")
    success: bool = Field(..., description="Успешность операции")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    tokens_used: Optional[int] = Field(None, description="Использованные токены")
    processing_time_seconds: Optional[float] = Field(None, description="Время обработки")
    created_at: datetime = Field(..., description="Дата создания")


class GenerationLogsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Ответ со списком логов генерации"""
    logs: List[GenerationLogResponse] = Field(..., description="Список логов")
    total: int = Field(..., description="Общее количество логов")


# Схемы для восстановления черновиков
class DraftErrorRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Запрос на отметку ошибки черновика"""
    error_message: str = Field(..., description="Сообщение об ошибке")
    error_step: str = Field(..., description="Шаг, на котором произошла ошибка")
    can_retry: bool = Field(True, description="Можно ли повторить операцию")


class RetryDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Ответ на попытку восстановления черновика"""
    success: bool = Field(..., description="Успешность операции")
    message: str = Field(..., description="Сообщение о результате")
    draft_id: int = Field(..., description="ID черновика")
    next_step: Optional[str] = Field(None, description="Следующий шаг для выполнения")
    status: Optional[str] = Field(None, description="Текущий статус черновика")


class FailedDraftsFilter(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Фильтры для получения черновиков с ошибками"""
    limit: int = Field(50, description="Максимальное количество результатов")
    include_recoverable_only: bool = Field(True, description="Включать только восстанавливаемые")
    user_id: Optional[int] = Field(None, description="Фильтр по пользователю")
    error_step: Optional[str] = Field(None, description="Фильтр по шагу ошибки")


class DraftRecoveryInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Информация о возможности восстановления черновика"""
    draft_id: int = Field(..., description="ID черновика")
    can_retry: bool = Field(..., description="Можно ли повторить операцию")
    retry_count: int = Field(..., description="Количество попыток")
    max_retries: int = Field(3, description="Максимальное количество попыток")
    last_error_step: Optional[str] = Field(None, description="Последний шаг с ошибкой")
    recovery_suggestions: List[str] = Field(default_factory=list, description="Рекомендации по восстановлению")


# Схемы для генерации статей из URL
class URLArticleParseRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Запрос на парсинг статьи по URL"""
    url: str = Field(..., description="URL статьи для парсинга")
    project: ProjectType = Field(..., description="Тип проекта для адаптации")


class URLArticleParseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Результат парсинга статьи из URL"""
    success: bool = Field(..., description="Успешность парсинга")
    url: str = Field(..., description="Исходный URL")
    content: str = Field(..., description="Извлеченный текст статьи")
    domain: str = Field(..., description="Домен источника")
    article_id: Optional[int] = Field(None, description="ID созданной статьи в БД")
    title: Optional[str] = Field(None, description="Заголовок статьи")
    error: Optional[str] = Field(None, description="Ошибка если парсинг не удался")


class URLArticleGenerationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Запрос на генерацию статьи из URL"""
    url: str = Field(..., description="URL статьи-источника")
    project: ProjectType = Field(..., description="Тип проекта")
    formatting_options: Optional[ArticleFormattingOptions] = Field(None, description="Параметры форматирования")
    generate_image: bool = Field(True, description="Генерировать ли изображение")


class URLArticleGenerationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    """Ответ с сгенерированной статьей из URL"""
    success: bool = Field(..., description="Успешность генерации")
    draft_id: Optional[int] = Field(None, description="ID созданного черновика")
    source_url: str = Field(..., description="URL источника")
    source_domain: str = Field(..., description="Домен источника")
    news_text: Optional[str] = Field(None, description="Сгенерированный текст")
    seo_title: Optional[str] = Field(None, description="SEO заголовок")
    seo_description: Optional[str] = Field(None, description="SEO описание")
    seo_keywords: Optional[List[str]] = Field(None, description="SEO ключевые слова")
    image_url: Optional[str] = Field(None, description="URL сгенерированного изображения")
    error: Optional[str] = Field(None, description="Ошибка если генерация не удалась")