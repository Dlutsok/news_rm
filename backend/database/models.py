"""
SQLModel модели для базы данных новостного агрегатора
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum


def moscow_now() -> datetime:
    """Получить текущее время в московском часовом поясе"""
    moscow_tz = timezone(timedelta(hours=3))
    return datetime.now(moscow_tz)


class SourceType(str, Enum):
    """Типы источников новостей"""
    RIA = "ria"
    MEDVESTNIK = "medvestnik"
    AIG = "aig"
    REMEDIUM = "remedium"
    RBC_MEDICAL = "rbc_medical"


class Article(SQLModel, table=True):
    """Модель статьи"""
    __tablename__ = "articles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=500, index=True)
    url: str = Field(unique=True, index=True, max_length=1000)
    content: Optional[str] = Field(default=None)
    source_site: SourceType = Field(index=True)
    
    # Метаданные статьи
    published_date: Optional[datetime] = Field(default=None, index=True)
    published_time: Optional[str] = Field(default=None, max_length=10)
    views_count: Optional[int] = Field(default=None)
    author: Optional[str] = Field(default=None, max_length=200)
    
    # Системные поля
    created_at: datetime = Field(default_factory=moscow_now, index=True)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Поля для анализа
    is_processed: bool = Field(default=False, index=True)
    processing_status: Optional[str] = Field(default=None, max_length=50)
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', source={self.source_site})>"


class SourceStats(SQLModel, table=True):
    """Статистика по источникам"""
    __tablename__ = "source_stats"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    source_site: SourceType = Field(unique=True, index=True)
    
    # Счетчики
    total_articles: int = Field(default=0)
    articles_today: int = Field(default=0)
    articles_this_week: int = Field(default=0)
    articles_this_month: int = Field(default=0)
    
    # Даты
    last_parsed_at: Optional[datetime] = Field(default=None)
    last_article_date: Optional[datetime] = Field(default=None)
    
    # Системные поля
    created_at: datetime = Field(default_factory=moscow_now)
    updated_at: datetime = Field(default_factory=moscow_now)
    
    def __repr__(self):
        return f"<SourceStats(source={self.source_site}, total={self.total_articles})>"


class ParseSession(SQLModel, table=True):
    """Сессия парсинга для отслеживания операций"""
    __tablename__ = "parse_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    source_site: SourceType = Field(index=True)
    
    # Параметры парсинга
    requested_articles: int = Field(default=0)
    parsed_articles: int = Field(default=0)
    saved_articles: int = Field(default=0)
    duplicate_articles: int = Field(default=0)
    
    # Статус
    status: str = Field(default="started", max_length=20)  # started, completed, failed
    error_message: Optional[str] = Field(default=None)
    
    # Временные метки
    started_at: datetime = Field(default_factory=moscow_now)
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[int] = Field(default=None)
    
    def __repr__(self):
        return f"<ParseSession(id={self.id}, source={self.source_site}, status={self.status})>"


# Pydantic модели для API (без table=True)
class ArticleRead(SQLModel):
    """Модель для чтения статьи через API"""
    id: int
    title: str
    url: str
    content: Optional[str] = None
    source_site: str  # Изменено с SourceType на str для API
    published_date: Optional[datetime] = None
    published_time: Optional[str] = None
    views_count: Optional[int] = None
    author: Optional[str] = None
    created_at: datetime
    is_processed: bool


class ArticleCreate(SQLModel):
    """Модель для создания статьи через API"""
    title: str
    url: str
    content: Optional[str] = None
    source_site: SourceType
    published_date: Optional[datetime] = None
    published_time: Optional[str] = None
    views_count: Optional[int] = None
    author: Optional[str] = None


class SourceStatsRead(SQLModel):
    """Модель для чтения статистики источника"""
    source_site: SourceType
    total_articles: int
    articles_today: int
    articles_this_week: int
    articles_this_month: int
    last_parsed_at: Optional[datetime] = None
    last_article_date: Optional[datetime] = None


class ParseSessionRead(SQLModel):
    """Модель для чтения сессии парсинга"""
    id: int
    source_site: SourceType
    requested_articles: int
    parsed_articles: int
    saved_articles: int
    duplicate_articles: int
    status: str
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


# Новые модели для генерации новостей
class UserRole(str, Enum):
    """Роли пользователей системы"""
    ADMIN = "admin"
    STAFF = "staff"  
    ANALYST = "analyst"


class ProjectType(str, Enum):
    """Типы проектов для генерации новостей"""
    GYNECOLOGY = "gynecology.school"
    THERAPY = "therapy.school"
    PEDIATRICS = "pediatrics.school"
    RUSMEDICAL = "rusmedical"


class NewsStatus(str, Enum):
    """Статусы новостей"""
    SUMMARY_PENDING = "summary_pending"
    CONFIRMED = "confirmed"
    GENERATED = "generated"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"


class User(SQLModel, table=True):
    """Модель пользователя системы"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    hashed_password: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.STAFF, index=True)
    project: Optional[str] = Field(default=None, index=True)  # Привязка к проекту
    
    # Системные поля
    created_at: datetime = Field(default_factory=moscow_now, index=True)
    updated_at: Optional[datetime] = Field(default=None)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role={self.role}, project={self.project})>"


class NewsGenerationDraft(SQLModel, table=True):
    """Черновик генерации новости"""
    __tablename__ = "news_generation_drafts"

    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="articles.id", index=True)
    project: str = Field(index=True, max_length=50)

    # Выжимка статьи
    summary: str = Field()
    facts: str = Field()  # JSON строка со списком фактов

    # Сгенерированный контент
    generated_news_text: Optional[str] = Field(default=None)
    generated_seo_title: Optional[str] = Field(default=None, max_length=200)
    generated_seo_description: Optional[str] = Field(default=None, max_length=500)
    generated_seo_keywords: Optional[str] = Field(default=None)  # JSON строка
    generated_image_prompt: Optional[str] = Field(default=None)
    generated_image_url: Optional[str] = Field(default=None, max_length=1000)
    generated_tg_post: Optional[str] = Field(default=None)  # текст анонса для Telegram

    # Статус процесса
    status: str = Field(default="summary_pending", index=True)

    # Отслеживание ошибок и восстановление
    last_error_message: Optional[str] = Field(default=None)  # Последнее сообщение об ошибке
    last_error_step: Optional[str] = Field(default=None, max_length=50)  # Шаг, на котором произошла ошибка
    last_error_at: Optional[datetime] = Field(default=None, index=True)  # Время последней ошибки
    can_retry: bool = Field(default=True, index=True)  # Можно ли повторить операцию
    retry_count: int = Field(default=0)  # Количество попыток

    # Информация о публикации
    is_published: bool = Field(default=False, index=True)
    published_project_code: Optional[str] = Field(default=None, max_length=10)  # GS, TS, PS
    published_project_name: Optional[str] = Field(default=None, max_length=100)  # Полное название проекта
    bitrix_id: Optional[int] = Field(default=None, index=True)  # ID в Bitrix CMS
    published_at: Optional[datetime] = Field(default=None, index=True)

    # Отложенная публикация
    scheduled_at: Optional[datetime] = Field(default=None, index=True)  # Время запланированной публикации (UTC)

    # Автор
    created_by: Optional[int] = Field(default=None, foreign_key="users.id", index=True)  # Пользователь который создал

    # Метаданные
    created_at: datetime = Field(default_factory=moscow_now, index=True)
    updated_at: datetime = Field(default_factory=moscow_now)
    
    def __repr__(self):
        return f"<NewsGenerationDraft(id={self.id}, article_id={self.article_id}, project={self.project}, status={self.status})>"


class GenerationLog(SQLModel, table=True):
    """Лог операций генерации для аналитики"""
    __tablename__ = "generation_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    draft_id: int = Field(foreign_key="news_generation_drafts.id", index=True)
    
    # Информация об операции
    operation_type: str = Field(max_length=50, index=True)  # summary, generation, image_regeneration
    model_used: str = Field(max_length=50)  # gpt-3.5-turbo-16k, gpt-4o
    
    # Результат
    success: bool = Field(default=True, index=True)
    error_message: Optional[str] = Field(default=None)
    
    # Метрики
    tokens_used: Optional[int] = Field(default=None)
    processing_time_seconds: Optional[float] = Field(default=None)
    
    # Временная метка
    created_at: datetime = Field(default_factory=moscow_now, index=True)
    
    def __repr__(self):
        return f"<GenerationLog(id={self.id}, operation={self.operation_type}, success={self.success})>"



class TelegramPost(SQLModel, table=True):
    """Модель Telegram поста для опубликованных новостей"""
    __tablename__ = "telegram_posts"

    id: Optional[int] = Field(default=None, primary_key=True)
    news_draft_id: int = Field(foreign_key="news_generation_drafts.id", index=True)

    # Настройки генерации
    hook_type: str = Field(max_length=50, index=True)  # question, shocking_fact, statistics, contradiction
    disclosure_level: str = Field(max_length=50)  # hint, main_idea, almost_all
    call_to_action: str = Field(max_length=50)  # curiosity, urgency, expertise
    include_image: bool = Field(default=True)

    # Сгенерированный контент
    post_text: str = Field(max_length=2000)  # Текст поста
    character_count: int = Field(default=0)  # Количество символов

    # Публикация в Telegram
    is_published: bool = Field(default=False, index=True)  # Опубликован ли пост
    published_at: Optional[datetime] = Field(default=None, index=True)  # Дата публикации
    telegram_message_id: Optional[int] = Field(default=None)  # ID сообщения в Telegram
    # Метаданные
    created_at: datetime = Field(default_factory=moscow_now, index=True)
    updated_at: datetime = Field(default_factory=moscow_now)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id", index=True)

    def __repr__(self):
        return f"<TelegramPost(id={self.id}, news_draft_id={self.news_draft_id}, hook={self.hook_type})>"


class PublicationLog(SQLModel, table=True):
    """Журнал публикаций в Bitrix (для аналитики)"""
    __tablename__ = "publication_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    draft_id: int = Field(index=True)
    username: Optional[str] = Field(default=None, max_length=100, index=True)
    project: Optional[str] = Field(default=None, max_length=200, index=True)
    bitrix_id: Optional[int] = Field(default=None, index=True)
    url: Optional[str] = Field(default=None, max_length=1000)
    image_url: Optional[str] = Field(default=None, max_length=1000)
    seo_title: Optional[str] = Field(default=None, max_length=300)
    cost_rub: int = Field(default=0)
    published_at: datetime = Field(default_factory=moscow_now, index=True)

    def __repr__(self):
        return f"<PublicationLog(draft_id={self.draft_id}, username={self.username}, cost={self.cost_rub})>"


class Publication(SQLModel, table=True):
    """Таблица публикаций статей в проекты (многие-к-многим)"""
    __tablename__ = "publications"

    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="articles.id", index=True)
    project_code: str = Field(max_length=10, index=True)  # GS, TS, PS, TEST, etc.
    project_name: Optional[str] = Field(default=None, max_length=100)
    bitrix_id: int = Field(index=True)
    published_at: datetime = Field(default_factory=moscow_now, index=True)
    published_by: Optional[int] = Field(default=None, foreign_key="users.id", index=True)

    # Уникальность: одна статья может быть опубликована в проекте только один раз
    __table_args__ = {"sqlite_autoincrement": True, "schema": None}

    def __repr__(self):
        return f"<Publication(id={self.id}, article_id={self.article_id}, project={self.project_code}, bitrix_id={self.bitrix_id})>"


# Pydantic модели для API
class NewsGenerationDraftRead(SQLModel):
    """Модель для чтения черновика через API"""
    id: int
    article_id: int
    project: str
    summary: str
    facts: str
    generated_news_text: Optional[str] = None
    generated_seo_title: Optional[str] = None
    generated_seo_description: Optional[str] = None
    generated_seo_keywords: Optional[str] = None
    generated_image_prompt: Optional[str] = None
    generated_image_url: Optional[str] = None
    status: str
    # Поля для отслеживания ошибок
    last_error_message: Optional[str] = None
    last_error_step: Optional[str] = None
    last_error_at: Optional[datetime] = None
    can_retry: bool = True
    retry_count: int = 0
    created_at: datetime
    updated_at: datetime


class GenerationLogRead(SQLModel):
    """Модель для чтения лога генерации"""
    id: int
    draft_id: int
    operation_type: str
    model_used: str
    success: bool
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    processing_time_seconds: Optional[float] = None
    created_at: datetime


class BitrixProjectSettings(SQLModel, table=True):
    """Настройки проектов Bitrix CMS"""
    __tablename__ = "bitrix_project_settings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_code: str = Field(unique=True, index=True, max_length=10)  # GS, TS, PS
    project_name: str = Field(max_length=100)  # gynecology.school, etc.
    display_name: str = Field(max_length=200)  # Гинекология и акушерство
    
    # API настройки
    api_url: Optional[str] = Field(default=None, max_length=500)
    api_token: Optional[str] = Field(default=None, max_length=500)
    iblock_id: Optional[int] = Field(default=38)
    
    # Дополнительные настройки
    is_active: bool = Field(default=True)
    description: Optional[str] = Field(default=None, max_length=1000)
    
    # Системные поля
    created_at: datetime = Field(default_factory=moscow_now)
    updated_at: Optional[datetime] = Field(default=None)
    
    def __repr__(self):
        return f"<BitrixProjectSettings(code={self.project_code}, name='{self.project_name}')>"


class AppSettings(SQLModel, table=True):
    """Общие настройки приложения"""
    __tablename__ = "app_settings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    setting_key: str = Field(unique=True, index=True, max_length=100)
    setting_value: Optional[str] = Field(default=None, max_length=2000)
    setting_type: str = Field(default="string", max_length=20)  # string, int, bool, json
    description: Optional[str] = Field(default=None, max_length=500)
    
    # Категория настройки
    category: str = Field(default="general", max_length=50, index=True)
    
    # Системные поля
    created_at: datetime = Field(default_factory=moscow_now)
    updated_at: Optional[datetime] = Field(default=None)
    
    def __repr__(self):
        return f"<AppSettings(key={self.setting_key}, value='{str(self.setting_value)[:30]}...')>"


# Pydantic модели для пользователей
class UserRead(SQLModel):
    """Модель для чтения пользователя через API"""
    id: int
    username: str
    role: UserRole
    project: Optional[str]
    created_at: datetime


class UserCreate(SQLModel):
    """Модель для создания пользователя через API"""
    username: str
    password: str
    role: UserRole = UserRole.STAFF
    project: Optional[ProjectType] = None


class UserLogin(SQLModel):
    """Модель для входа в систему"""
    username: str
    password: str


class Token(SQLModel):
    """Модель токена авторизации"""
    access_token: str
    token_type: str = "bearer"


class TokenData(SQLModel):
    """Данные токена"""
    username: Optional[str] = None


class ExpenseType(str, Enum):
    """Типы расходов"""
    NEWS_CREATION = "news_creation"  # 40 рублей
    PHOTO_REGENERATION = "photo_regeneration"  # 10 рублей
    GPT_MESSAGE = "gpt_message"  # 5 рублей
    TELEGRAM_POST = "telegram_post"  # 20 рублей


class Expense(SQLModel, table=True):
    """Модель расходов"""
    __tablename__ = "expenses"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    project: str = Field(index=True, max_length=50)
    expense_type: str = Field(index=True, max_length=50)
    amount: float = Field(index=True)  # Сумма в рублях
    description: Optional[str] = Field(default=None, max_length=500)
    
    # Дополнительные данные
    related_article_id: Optional[int] = Field(default=None, foreign_key="articles.id")
    related_session_id: Optional[str] = Field(default=None, max_length=100)  # ID сессии GPT или другой операции
    
    # Системные поля
    created_at: datetime = Field(default_factory=moscow_now, index=True)
    updated_at: Optional[datetime] = Field(default=None)
    
    def __repr__(self):
        return f"<Expense(id={self.id}, user_id={self.user_id}, project={self.project}, type={self.expense_type}, amount={self.amount})>"


# Убираем неправильную связь - она должна быть определена в самой модели User


# Pydantic модели для API расходов
class ExpenseRead(SQLModel):
    """Модель для чтения расходов"""
    id: int
    user_id: int
    project: ProjectType
    expense_type: ExpenseType
    amount: float
    description: Optional[str]
    related_article_id: Optional[int]
    related_session_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Дополнительные поля для API
    user_name: Optional[str] = None
    project_name: Optional[str] = None
    expense_type_name: Optional[str] = None


class ExpenseCreate(SQLModel):
    """Модель для создания расходов"""
    user_id: int
    project: ProjectType
    expense_type: ExpenseType
    amount: float
    description: Optional[str] = None
    related_article_id: Optional[int] = None
    related_session_id: Optional[str] = None


class ExpenseSummary(SQLModel):
    """Сводка расходов"""
    total_amount: float
    expenses_count: int
    by_project: dict
    by_user: dict
    by_type: dict


# Pydantic модели для API Telegram постов
class TelegramPostRead(SQLModel):
    """Модель для чтения Telegram поста через API"""
    id: int
    news_draft_id: int
    hook_type: str
    disclosure_level: str
    call_to_action: str
    include_image: bool
    post_text: str
    character_count: int
    is_published: bool
    published_at: Optional[datetime]
    telegram_message_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None


class TelegramPostCreate(SQLModel):
    """Модель для создания Telegram поста"""
    news_draft_id: int
    hook_type: str = "question"
    disclosure_level: str = "hint"
    call_to_action: str = "curiosity"
    include_image: bool = True


class TelegramPostSettings(SQLModel):
    """Настройки для генерации Telegram поста"""
    hook_type: str = "question"
    disclosure_level: str = "hint"
    call_to_action: str = "curiosity"
    include_image: bool = True
    article_url: Optional[str] = None
    link_button_text: str = "📖 Читать полную статью"