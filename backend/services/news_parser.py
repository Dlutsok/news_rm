import aiohttp
import asyncio
import ssl
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin, urlparse
import logging

from models.schemas import NewsSource, PlatformType
from core.config import settings

logger = logging.getLogger(__name__)

class NewsParserService:
    def __init__(self):
        self.base_url = settings.MEDVESTNIK_BASE_URL
        self.news_url = settings.MEDVESTNIK_NEWS_URL
        self.session = None
        
    async def __aenter__(self):
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
        if self.session:
            await self.session.close()
    
    async def parse_news_list(self, max_articles: int = 10, date_filter: Optional[str] = None, fetch_full_content: bool = True) -> List[NewsSource]:
        """Парсинг списка новостей с главной страницы medvestnik.ru"""
        try:
            # Используем правильный URL для страницы новостей
            news_list_url = "https://medvestnik.ru/content/roubric/news"
            
            async with self.session.get(news_list_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch news list: {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                news_items = []
                seen_urls = set()
                seen_titles = set()
                
                # Ищем ссылки на статьи с правильным селектором для medvestnik.ru
                # Формат: <a class="ui" href="/content/news/...">
                article_links = soup.find_all('a', {'class': 'ui', 'href': re.compile(r'/content/news/')})
                
                logger.info(f"Found {len(article_links)} news article links")
                
                for link in article_links:
                    try:
                        # Получаем URL статьи
                        href = link.get('href')
                        if not href:
                            continue
                            
                        full_url = urljoin(self.base_url, href)
                        
                        # Проверяем на дубли по URL
                        if full_url in seen_urls:
                            continue
                        seen_urls.add(full_url)
                        
                        # Извлекаем заголовок из превью
                        title_elem = link.find('h3', class_='ui header no-marged')
                        title = title_elem.get_text(strip=True) if title_elem else "Без заголовка"
                        
                        # Проверяем на дубли по заголовку
                        if title in seen_titles:
                            continue
                        seen_titles.add(title)
                        
                        # Извлекаем краткое описание из превью
                        announce_elem = link.find('span', class_='item-announce-url')
                        preview_content = announce_elem.get_text(strip=True) if announce_elem else ""
                        
                        # Если нужен полный контент, парсим статью с метаданными
                        full_content = ""
                        published_date = None
                        published_time = None
                        views_count = None
                        
                        if fetch_full_content:
                            full_content, published_date, published_time, views_count = await self._fetch_full_article_with_metadata(full_url)
                        
                        # Используем полный контент если есть, иначе превью
                        content = full_content if full_content else preview_content
                        
                        # Создаем объект новости с метаданными
                        news_item = NewsSource(
                            title=title,
                            url=full_url,
                            content=content,
                            published_date=published_date,
                            published_time=published_time,
                            views_count=views_count,
                            source_site="medvestnik.ru"
                        )
                        
                        if self._is_relevant_news(news_item, date_filter):
                            news_items.append(news_item)
                            logger.info(f"Added news: {title[:50]}...")
                            
                            # Добавляем задержку между запросами
                            await asyncio.sleep(0.5)
                            
                            # Ограничиваем количество статей
                            if len(news_items) >= max_articles:
                                break
                                
                    except Exception as e:
                        logger.warning(f"Error parsing article link: {e}")
                        continue
                
                logger.info(f"Successfully parsed {len(news_items)} unique news articles")
                return news_items
                
        except Exception as e:
            logger.error(f"Error parsing news list: {e}")
            return []
    
    async def _parse_article_preview(self, article_element, fetch_full_content: bool = True) -> Optional[NewsSource]:
        """Парсинг превью статьи из элемента списка"""
        try:
            # Извлекаем ссылку
            link_elem = article_element if article_element.name == 'a' else article_element.find('a')
            if not link_elem:
                return None
                
            href = link_elem.get('href')
            if not href:
                return None
                
            # Формируем полную ссылку
            full_url = urljoin(self.base_url, href)
            
            # Извлекаем заголовок
            title_elem = (
                article_element.find(['h1', 'h2', 'h3', 'h4']) or
                link_elem.find(['h1', 'h2', 'h3', 'h4']) or
                link_elem
            )
            title = title_elem.get_text(strip=True) if title_elem else "Без заголовка"
            
            # Извлекаем краткое содержание
            content_elem = article_element.find(['p', 'div'], class_=re.compile(r'excerpt|summary|description'))
            content = content_elem.get_text(strip=True) if content_elem else ""
            
            # Если контента нет в превью, получаем полную статью (только если разрешено)
            if fetch_full_content and (not content or len(content) < 50):
                full_content = await self._fetch_full_article(full_url)
                content = full_content[:500] + "..." if full_content else content
            
            # Извлекаем дату (если есть)
            date_elem = article_element.find(['time', 'span'], class_=re.compile(r'date|time'))
            published_date = self._parse_date(date_elem.get_text(strip=True)) if date_elem else None
            
            return NewsSource(
                title=title,
                url=full_url,
                content=content,
                published_date=published_date,
                source_site="medvestnik.ru"
            )
            
        except Exception as e:
            logger.warning(f"Error parsing article preview: {e}")
            return None
    
    async def _extract_article_metadata(self, soup: BeautifulSoup) -> tuple[Optional[datetime], Optional[str], Optional[int]]:
        """Извлечение метаданных статьи: дата, время, просмотры"""
        published_date = None
        published_time = None
        views_count = None
        
        try:
            # Ищем блок с метаданными
            metadata_block = soup.find('div', class_='ui list muted horizontal spaced-bottom-quorter middle aligned')
            
            if metadata_block:
                items = metadata_block.find_all('div', class_='item')
                
                for item in items:
                    content_div = item.find('div', class_='content')
                    if content_div:
                        description_div = content_div.find('div', class_='description')
                        if description_div:
                            # Проверяем иконку календаря для даты
                            calendar_icon = description_div.find('i', class_='icon calendar alternate outline')
                            if calendar_icon:
                                date_span = description_div.find('span')
                                if date_span:
                                    date_text = date_span.get_text(strip=True)
                                    published_date = self._parse_date(date_text)
                            
                            # Проверяем иконку часов для времени
                            clock_icon = description_div.find('i', class_='icon clock outline')
                            if clock_icon:
                                time_span = description_div.find('span')
                                if time_span:
                                    published_time = time_span.get_text(strip=True)
                            
                            # Проверяем иконку глаза для просмотров
                            eye_icon = description_div.find('i', class_='icon eye outline')
                            if eye_icon:
                                views_span = description_div.find('span', class_='c-views-counter')
                                if views_span:
                                    # Ищем текст с количеством просмотров
                                    text_span = views_span.find('span', class_='text')
                                    if text_span:
                                        views_text = text_span.get_text(strip=True)
                                        try:
                                            views_count = int(views_text)
                                        except ValueError:
                                            pass
            
            logger.info(f"Extracted metadata - Date: {published_date}, Time: {published_time}, Views: {views_count}")
            return published_date, published_time, views_count
            
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
            return None, None, None

    async def _fetch_full_article_with_metadata(self, url: str, max_retries: int = 3) -> tuple[Optional[str], Optional[datetime], Optional[str], Optional[int]]:
        """Получение полного текста статьи с метаданными с medvestnik.ru"""
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                async with self.session.get(url, timeout=timeout) as response:
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None, None, None, None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Извлекаем метаданные
                    published_date, published_time, views_count = await self._extract_article_metadata(soup)
                    
                    # Удаляем ненужные элементы перед парсингом
                    for element in soup.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
                        element.decompose()
                    
                    # Удаляем рекламные блоки и баннеры
                    for element in soup.find_all(class_=re.compile(r'bm-banner|injected-block|ad|banner|promo')):
                        element.decompose()
                    
                    content = ""
                    
                    # Ищем основной контент статьи в правильном контейнере
                    # Согласно структуре medvestnik.ru: <div class="c-typography-text">
                    content_container = soup.find('div', class_='c-typography-text')
                    
                    if content_container:
                        # Извлекаем все параграфы из контейнера
                        paragraphs = content_container.find_all('p')
                        content_parts = []
                        
                        for p in paragraphs:
                            p_text = p.get_text(strip=True)
                            
                            # Фильтруем параграфы: минимум 20 символов, исключаем служебный текст
                            if (len(p_text) > 20 and 
                                not re.match(r'^\d{2}\.\d{2}\.\d{4}', p_text) and
                                not any(skip_word in p_text.lower() for skip_word in [
                                    'подробнее:', 'читать далее', 'источник:', 'фото:',
                                    'войти', 'регистрация', 'подписаться', 'следить',
                                    'все права защищены', 'copyright', 'реклама'
                                ])):
                                content_parts.append(p_text)
                        
                        if content_parts:
                            # Объединяем параграфы с двойными переносами строк для сохранения структуры
                            content = '\n\n'.join(content_parts)
                            logger.info(f"Extracted {len(content)} characters from article")
                        else:
                            # Если параграфы не найдены, берем весь текст контейнера
                            content = content_container.get_text(strip=True)
                    
                    # Если основной контейнер не найден, пробуем альтернативные селекторы
                    if not content or len(content) < 100:
                        alternative_selectors = [
                            'div.contents div.c-typography-text',
                            'div.contents',
                            '.article-content',
                            '.news-content',
                            'article .content',
                            'main'
                        ]
                        
                        for selector in alternative_selectors:
                            content_elem = soup.select_one(selector)
                            if content_elem:
                                paragraphs = content_elem.find_all('p')
                                if paragraphs:
                                    content_parts = []
                                    for p in paragraphs:
                                        p_text = p.get_text(strip=True)
                                        if len(p_text) > 20:
                                            content_parts.append(p_text)
                                    
                                    if content_parts:
                                        # Объединяем параграфы с двойными переносами строк
                                        content = '\n\n'.join(content_parts)
                                        break
                                else:
                                    # Если нет параграфов, берем весь текст
                                    elem_text = content_elem.get_text(strip=True)
                                    if len(elem_text) > 100:
                                        content = elem_text
                                        break
                    
                    # Финальная очистка контента
                    if content:
                        # Удаляем лишние пробелы внутри строк, но сохраняем переносы между абзацами
                        content = re.sub(r'[ \t]+', ' ', content)  # Убираем лишние пробелы и табы
                        content = re.sub(r'\n{3,}', '\n\n', content)  # Убираем лишние переносы (больше 2)
                        content = content.strip()
                        
                        # Ограничиваем длину контента
                        if len(content) > 6000:
                            content = content[:6000] + "..."
                        
                        logger.info(f"Successfully extracted article content: {len(content)} characters")
                        return content, published_date, published_time, views_count
                    else:
                        logger.warning(f"No content found for {url}")
                        return None, published_date, published_time, views_count
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    return None, None, None, None
            except Exception as e:
                logger.warning(f"Error fetching article {url} (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return None, None, None, None
        
        return None, None, None, None

    async def _fetch_full_article(self, url: str) -> Optional[str]:
        """Получение полного текста статьи с medvestnik.ru"""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Добавляем небольшую задержку между запросами
                if attempt > 0:
                    await asyncio.sleep(retry_delay)
                
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
                        
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Удаляем ненужные элементы перед парсингом
                    for element in soup.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
                        element.decompose()
                    
                    # Удаляем рекламные блоки и баннеры
                    for element in soup.find_all(class_=re.compile(r'bm-banner|injected-block|ad|banner|promo')):
                        element.decompose()
                    
                    content = ""
                    
                    # Ищем основной контент статьи в правильном контейнере
                    # Согласно структуре medvestnik.ru: <div class="c-typography-text">
                    content_container = soup.find('div', class_='c-typography-text')
                    
                    if content_container:
                        # Извлекаем все параграфы из контейнера
                        paragraphs = content_container.find_all('p')
                        content_parts = []
                        
                        for p in paragraphs:
                            p_text = p.get_text(strip=True)
                            
                            # Фильтруем параграфы: минимум 20 символов, исключаем служебный текст
                            if (len(p_text) > 20 and 
                                not re.match(r'^\d{2}\.\d{2}\.\d{4}', p_text) and
                                not any(skip_word in p_text.lower() for skip_word in [
                                    'подробнее:', 'читать далее', 'источник:', 'фото:',
                                    'войти', 'регистрация', 'подписаться', 'следить',
                                    'все права защищены', 'copyright', 'реклама'
                                ])):
                                content_parts.append(p_text)
                        
                        if content_parts:
                            # Объединяем параграфы с двойными переносами строк для сохранения структуры
                            content = '\n\n'.join(content_parts)
                            logger.info(f"Extracted {len(content)} characters from article")
                        else:
                            # Если параграфы не найдены, берем весь текст контейнера
                            content = content_container.get_text(strip=True)
                    
                    # Если основной контейнер не найден, пробуем альтернативные селекторы
                    if not content or len(content) < 100:
                        alternative_selectors = [
                            'div.contents div.c-typography-text',
                            'div.contents',
                            '.article-content',
                            '.news-content',
                            'article .content',
                            'main'
                        ]
                        
                        for selector in alternative_selectors:
                            content_elem = soup.select_one(selector)
                            if content_elem:
                                paragraphs = content_elem.find_all('p')
                                if paragraphs:
                                    content_parts = []
                                    for p in paragraphs:
                                        p_text = p.get_text(strip=True)
                                        if len(p_text) > 20:
                                            content_parts.append(p_text)
                                    
                                    if content_parts:
                                        # Объединяем параграфы с двойными переносами строк
                                        content = '\n\n'.join(content_parts)
                                        break
                                else:
                                    # Если нет параграфов, берем весь текст
                                    elem_text = content_elem.get_text(strip=True)
                                    if len(elem_text) > 100:
                                        content = elem_text
                                        break
                    
                    # Финальная очистка контента
                    if content:
                        # Удаляем лишние пробелы внутри строк, но сохраняем переносы между абзацами
                        content = re.sub(r'[ \t]+', ' ', content)  # Убираем лишние пробелы и табы
                        content = re.sub(r'\n{3,}', '\n\n', content)  # Убираем лишние переносы (больше 2)
                        content = content.strip()
                        
                        # Ограничиваем длину контента
                        if len(content) > 6000:
                            content = content[:6000] + "..."
                        
                        logger.info(f"Successfully extracted article content: {len(content)} characters")
                        return content
                    else:
                        logger.warning(f"No content found for {url}")
                        return None
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    return None
            except Exception as e:
                logger.warning(f"Error fetching article {url} (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return None
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Парсинг даты из строки"""
        if not date_str:
            return None
            
        try:
            # Различные форматы дат
            date_patterns = [
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # DD.MM.YYYY
                r'(\d{4})-(\d{1,2})-(\d{1,2})',   # YYYY-MM-DD
                r'(\d{1,2})/(\d{1,2})/(\d{4})',   # DD/MM/YYYY
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_str)
                if match:
                    if '.' in date_str:
                        day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day))
                    elif '-' in date_str:
                        year, month, day = match.groups()
                        return datetime(int(year), int(month), int(day))
                    elif '/' in date_str:
                        day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day))
            
            return None
            
        except Exception:
            return None
    
    def _is_relevant_news(self, news: NewsSource, date_filter: Optional[str]) -> bool:
        """Проверка релевантности новости по дате"""
        if not date_filter or not news.published_date:
            return True
            
        now = datetime.now()
        
        if date_filter == "today":
            return news.published_date.date() == now.date()
        elif date_filter == "week":
            return news.published_date >= now - timedelta(days=7)
        elif date_filter == "month":
            return news.published_date >= now - timedelta(days=30)
            
        return True
    
    def _deduplicate_news(self, news_list: List[NewsSource]) -> List[NewsSource]:
        """Удаление дублированных новостей по URL и заголовку"""
        unique_news = []
        seen_urls = set()
        seen_titles = set()
        
        for news in news_list:
            if news.url not in seen_urls and news.title not in seen_titles:
                seen_urls.add(news.url)
                seen_titles.add(news.title)
                unique_news.append(news)
        
        return unique_news
    
    def filter_by_platform_relevance(self, news_list: List[NewsSource], platform: PlatformType) -> List[NewsSource]:
        """Фильтрация новостей по релевантности для конкретной платформы"""
        platform_config = settings.PLATFORMS.get(platform.value, {})
        topics = platform_config.get("topics", [])
        
        if not topics:
            return self._deduplicate_news(news_list)
        
        relevant_news = []
        seen_urls = set()
        seen_titles = set()
        
        for news in news_list:
            # Проверяем на дубли
            if news.url in seen_urls or news.title in seen_titles:
                continue
                
            relevance_score = 0
            text_to_check = f"{news.title} {news.content}".lower()
            
            for topic in topics:
                if topic.lower() in text_to_check:
                    relevance_score += 1
            
            # Добавляем новость если найдено хотя бы одно совпадение
            if relevance_score > 0:
                seen_urls.add(news.url)
                seen_titles.add(news.title)
                relevant_news.append(news)
        
        # Сортируем по релевантности (можно добавить более сложную логику)
        return relevant_news
    
    async def parse_news(self, limit: int = 10, days_back: int = 7) -> List[NewsSource]:
        """Основной метод парсинга новостей"""
        if not self.session:
            async with self:
                return await self.parse_news_list(max_articles=limit)
        else:
            return await self.parse_news_list(max_articles=limit)
    
    async def filter_by_platform(self, news_list: List[NewsSource], platform: str) -> List[NewsSource]:
        """Фильтрация новостей по платформе"""
        platform_config = settings.PLATFORMS.get(platform, {})
        topics = platform_config.get("topics", [])
        
        if not topics:
            return self._deduplicate_news(news_list)
        
        relevant_news = []
        seen_urls = set()
        seen_titles = set()
        
        for news in news_list:
            # Проверяем на дубли
            if news.url in seen_urls or news.title in seen_titles:
                continue
                
            relevance_score = 0
            text_to_check = f"{news.title} {news.content}".lower()
            
            for topic in topics:
                if topic.lower() in text_to_check:
                    relevance_score += 1
            
            # Добавляем новость если найдено хотя бы одно совпадение
            if relevance_score > 0:
                seen_urls.add(news.url)
                seen_titles.add(news.title)
                relevant_news.append(news)
        
        return relevant_news