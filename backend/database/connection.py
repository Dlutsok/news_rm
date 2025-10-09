"""
Подключение к базе данных PostgreSQL через SQLModel
"""

import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool
import logging
from dotenv import load_dotenv
import pathlib

# Загружаем .env файл из корня проекта
env_path = pathlib.Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

# Конфигурация базы данных
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres@localhost:5432/news_aggregator"
)

# Создаем движок базы данных
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Установить True для отладки SQL запросов
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Установить True для отладки SQL запросов
        pool_pre_ping=True,  # Проверка соединения перед использованием
        pool_recycle=3600,   # Пересоздание соединений каждый час
    )


def create_db_and_tables():
    """Создание всех таблиц в базе данных"""
    try:
        # Импортируем все модели, чтобы они были зарегистрированы
        from database.models import (
            Article, SourceStats, ParseSession, NewsGenerationDraft, GenerationLog,
            User, BitrixProjectSettings, AppSettings, PublicationLog, TelegramPost,
            Publication, Expense
        )
        
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_session():
    """Получение сессии базы данных"""
    with Session(engine) as session:
        yield session


def get_db_session() -> Session:
    """Получение сессии базы данных (синхронная версия)"""
    return Session(engine)


# Для тестирования - создание in-memory SQLite базы
def create_test_engine():
    """Создание тестовой базы данных в памяти"""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True
    )
    return test_engine


def init_database():
    """Инициализация базы данных при запуске приложения"""
    try:
        logger.info("Initializing database...")
        logger.info(f"Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
        
        # Создаем таблицы
        create_db_and_tables()
        
        # Проверяем подключение
        with Session(engine) as session:
            from sqlmodel import text
            session.exec(text("SELECT 1")).first()
            logger.info("Database connection successful")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


# Контекстный менеджер для работы с транзакциями
class DatabaseSession:
    """Контекстный менеджер для работы с базой данных"""
    
    def __init__(self):
        self.session = None
    
    def __enter__(self) -> Session:
        self.session = Session(engine)
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
            logger.error(f"Database transaction rolled back: {exc_val}")
        else:
            self.session.commit()
        self.session.close()


# Декоратор для автоматического управления сессией
def with_db_session(func):
    """Декоратор для автоматического создания и закрытия сессии БД"""
    def wrapper(*args, **kwargs):
        with DatabaseSession() as session:
            return func(session, *args, **kwargs)
    return wrapper