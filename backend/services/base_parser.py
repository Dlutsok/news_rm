from abc import ABC, abstractmethod
import aiohttp
import ssl
from typing import List, Optional
from datetime import datetime
import logging
from bs4 import BeautifulSoup

from models.schemas import NewsSource

logger = logging.getLogger(__name__)

class BaseNewsParser(ABC):
    """Базовый класс для всех парсеров новостей"""
    
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.name = source_name  # Добавляем атрибут name для совместимости
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        """Инициализация HTTP сессии"""
        # Создаем SSL контекст с отключенной проверкой сертификатов
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Создаем коннектор с отключенной SSL проверкой
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def parse_news_list(self, max_articles: int = 10, date_filter: Optional[str] = None, fetch_full_content: bool = True) -> List[NewsSource]:
        """Парсинг списка новостей с главной страницы"""
        pass
    
    @abstractmethod
    async def _fetch_full_article(self, url: str) -> str:
        """Получение полного контента статьи"""
        pass
    
    @abstractmethod
    async def _extract_article_metadata(self, soup: BeautifulSoup) -> tuple[Optional[datetime], Optional[str], Optional[int]]:
        """Извлечение метаданных статьи: дата, время, просмотры"""
        pass
    
    def _is_relevant_news(self, news_item: NewsSource, date_filter: Optional[str] = None) -> bool:
        """Проверка релевантности новости по дате"""
        if not date_filter:
            return True
            
        if not news_item.published_date:
            return True  # Если дата неизвестна, включаем новость
            
        now = datetime.now()
        
        if date_filter == "today":
            return news_item.published_date.date() == now.date()
        elif date_filter == "week":
            return (now - news_item.published_date).days <= 7
        elif date_filter == "month":
            return (now - news_item.published_date).days <= 30
            
        return True
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Парсинг даты из строки"""
        if not date_str:
            return None
            
        # Сначала пробуем ISO формат (для AIG Journal)
        try:
            # Поддержка ISO 8601 формата с timezone
            if 'T' in date_str and ('+' in date_str or 'Z' in date_str):
                from dateutil import parser
                return parser.parse(date_str).replace(tzinfo=None)
        except Exception:
            pass
            
        # Общие форматы дат
        date_formats = [
            "%d.%m.%Y",
            "%d/%m/%Y", 
            "%Y-%m-%d",
            "%d %B %Y",
            "%d %b %Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S"
        ]
        
        # Русские месяцы
        russian_months = {
            'января': 'January', 'февраля': 'February', 'марта': 'March',
            'апреля': 'April', 'мая': 'May', 'июня': 'June',
            'июля': 'July', 'августа': 'August', 'сентября': 'September',
            'октября': 'October', 'ноября': 'November', 'декабря': 'December'
        }
        
        # Заменяем русские месяцы на английские
        for ru_month, en_month in russian_months.items():
            date_str = date_str.replace(ru_month, en_month)
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str.strip(), date_format)
            except ValueError:
                continue
                
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    async def get_parser_info(self) -> dict:
        """Получение информации о парсере"""
        return {
            "source_name": self.source_name,
            "base_url": self.base_url,
            "status": "active"
        }