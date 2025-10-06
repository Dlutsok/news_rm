import asyncio
import re
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
from urllib.parse import urljoin
import logging

from models.schemas import NewsSource
from services.base_parser import BaseNewsParser

logger = logging.getLogger(__name__)

class AigParser(BaseNewsParser):
    """Парсер для aig-journal.ru"""
    
    def __init__(self):
        super().__init__("aig", "https://aig-journal.ru")
        self.name = "aig"
        self.news_url = "https://aig-journal.ru/content/roubric/news"
    
    async def parse_news_list(self, max_articles: int = 50, date_filter: Optional[str] = None, fetch_full_content: bool = True) -> List[NewsSource]:
        """Парсинг списка новостей с главной страницы aig-journal.ru с поддержкой пагинации"""
        try:
            logger.info(f"Starting parse_news_list for aig-journal with max_articles={max_articles}")
            logger.info(f"Session status: {self.session is not None and not getattr(self.session, 'closed', True)}")
            
            if not self.session or getattr(self.session, 'closed', True):
                logger.error("Session is not initialized or closed")
                return []
            
            news_items = []
            seen_urls = set()
            seen_titles = set()
            page = 1
            max_pages = 10  # Ограничение по количеству страниц для безопасности
            
            while page <= max_pages and len(news_items) < max_articles:
                # Формируем URL для текущей страницы
                if page == 1:
                    url = self.news_url
                else:
                    url = f"{self.news_url}?page={page}"
                
                logger.info(f"Parsing page {page}: {url}")
                
                async with self.session.get(url) as response:
                    logger.info(f"HTTP response status for page {page}: {response.status}")
                    if response.status != 200:
                        logger.error(f"Failed to fetch news list page {page}: {response.status}")
                        break
                    
                    html = await response.text()
                    logger.info(f"Received HTML content length for page {page}: {len(html)}")
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем ссылки на статьи - используем паттерны /content/medarticles/ и /content/news/
                    article_links = soup.find_all('a', {'href': re.compile(r'/content/(medarticles|news)/')})
                    
                    logger.info(f"Found {len(article_links)} news article links on page {page}")
                    
                    page_articles_count = 0
                    
                    for link in article_links:
                        try:
                            # Получаем URL статьи
                            href = link.get('href')
                            if not href:
                                logger.debug("Href attribute not found in article link")
                                continue
                                
                            full_url = urljoin(self.base_url, href)
                            
                            # Проверяем на дубли по URL
                            if full_url in seen_urls:
                                continue
                            seen_urls.add(full_url)
                            
                            # Извлекаем заголовок из ссылки
                            title = link.get_text(strip=True)
                            
                            # Если заголовок пустой, пробуем найти в родительском элементе
                            if not title:
                                parent = link.parent
                                if parent:
                                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4'])
                                    title = title_elem.get_text(strip=True) if title_elem else ""
                            
                            # Если заголовок все еще пустой, генерируем его из URL
                            if not title:
                                title = href.split('/')[-1].replace('.html', '').replace('-', ' ').title()
                            
                            # Проверяем на дубли по заголовку
                            if title in seen_titles:
                                continue
                            seen_titles.add(title)
                            
                            # Если нужен полный контент, парсим статью с метаданными
                            full_content = ""
                            published_date = None
                            published_time = None
                            views_count = None
                            author = None
                            
                            if fetch_full_content:
                                full_content, published_date, published_time, views_count, author = await self._fetch_full_article_with_metadata(full_url)
                            
                            # Используем полный контент если есть, иначе заголовок как превью
                            content = full_content if full_content else title
                            
                            # Создаем объект новости с метаданными
                            news_item = NewsSource(
                                title=title,
                                url=full_url,
                                content=content,
                                published_date=published_date,
                                published_time=published_time,
                                views_count=views_count,
                                author=author,
                                source_site="aig-journal.ru"
                            )
                            
                            if self._is_relevant_news(news_item, date_filter):
                                news_items.append(news_item)
                                page_articles_count += 1
                                logger.info(f"Added news from page {page}: {title[:50]}...")
                                
                                # Добавляем задержку между запросами
                                await asyncio.sleep(0.5)
                                
                                # Ограничиваем количество статей
                                if len(news_items) >= max_articles:
                                    break
                                    
                        except Exception as e:
                            logger.warning(f"Error parsing article link on page {page}: {e}")
                            continue
                    
                    logger.info(f"Added {page_articles_count} articles from page {page}")
                    
                    # Если достигли максимального количества статей, прекращаем парсинг
                    if len(news_items) >= max_articles:
                        logger.info(f"Reached max articles limit ({max_articles}), stopping pagination")
                        break
                    
                    # Переходим к следующей странице
                    page += 1
                    
                    # Добавляем задержку между страницами
                    await asyncio.sleep(1.0)
            
            logger.info(f"Successfully parsed {len(news_items)} unique news articles from {page-1} pages")
            return news_items
                
        except Exception as e:
            logger.error(f"Error parsing news list: {e}")
            return []
    
    async def _fetch_full_article(self, url: str) -> str:
        """Получение полного контента статьи"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch article {url}: {response.status}")
                    return ""
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Удаляем ненужные элементы
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()
                
                # Ищем основной контент статьи
                content_parts = []
                
                # Специфичная логика для AIG Journal - собираем контент из определенных контейнеров
                lead_container = soup.find('div', class_='c-typography-lead')
                text_container = soup.find('div', class_='c-typography-text')
                
                # Добавляем вводный текст (lead)
                if lead_container:
                    lead_text = lead_container.get_text(strip=True)
                    if lead_text and len(lead_text) > 20:
                        content_parts.append(lead_text)
                
                # Добавляем основной текст
                if text_container:
                    # Ищем все параграфы в основном контейнере
                    paragraphs = text_container.find_all('p')
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if (text and len(text) > 20 and 
                            not any(skip_word in text.lower() for skip_word in 
                                   ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться', 'читать далее', 'подробнее'])):
                            content_parts.append(text)
                
                # Если специфичные контейнеры не найдены, используем общие селекторы
                if not content_parts:
                    general_selectors = [
                        {'tag': 'div', 'class': 'article-text'},
                        {'tag': 'div', 'class': 'article-content'},
                        {'tag': 'div', 'class': 'content-text'},
                        {'tag': 'div', 'class': 'post-content'},
                        {'tag': 'div', 'class': 'entry-content'},
                        {'tag': 'article'},
                        {'tag': 'main'},
                    ]
                    
                    for selector in general_selectors:
                        if 'class' in selector:
                            container = soup.find(selector['tag'], class_=selector['class'])
                        else:
                            container = soup.find(selector['tag'])
                            
                        if container:
                            # Ищем все параграфы и div с текстом внутри контейнера
                            text_elements = container.find_all(['p', 'div'], recursive=True)
                            for elem in text_elements:
                                # Пропускаем элементы с определенными классами
                                if elem.get('class'):
                                    classes = ' '.join(elem.get('class', []))
                                    if any(skip_class in classes.lower() for skip_class in 
                                          ['nav', 'menu', 'sidebar', 'footer', 'header', 'ad', 'banner', 'social', 'btn', 'button']):
                                        continue
                                
                                text = elem.get_text(strip=True)
                                if (text and len(text) > 20 and 
                                    not any(skip_word in text.lower() for skip_word in 
                                           ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться', 'читать далее', 'подробнее'])):
                                    content_parts.append(text)
                            
                            if content_parts:
                                break
                
                # Если основной метод не сработал, ищем все параграфы на странице
                if not content_parts:
                    all_paragraphs = soup.find_all('p')
                    for p in all_paragraphs:
                        text = p.get_text(strip=True)
                        if (text and len(text) > 20 and 
                            not any(skip_word in text.lower() for skip_word in 
                                   ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться', 'читать далее'])):
                            content_parts.append(text)
                
                # Если все еще нет контента, ищем в любых div с текстом
                if not content_parts:
                    all_divs = soup.find_all('div')
                    for div in all_divs:
                        text = div.get_text(strip=True)
                        if (text and len(text) > 50 and len(text) < 1000 and
                            not any(skip_word in text.lower() for skip_word in 
                                   ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться'])):
                            content_parts.append(text)
                
                # Убираем дубли и объединяем
                unique_parts = []
                seen_texts = set()
                for part in content_parts:
                    if part not in seen_texts and len(part) > 20:
                        unique_parts.append(part)
                        seen_texts.add(part)
                
                return '\n\n'.join(unique_parts[:8])  # Ограничиваем количество абзацев
                
        except Exception as e:
            logger.error(f"Error fetching full article {url}: {e}")
            return ""
    
    async def _extract_content_from_soup(self, soup: BeautifulSoup) -> str:
        """Извлечение контента из BeautifulSoup объекта"""
        try:
            # Удаляем ненужные элементы
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Ищем основной контент статьи
            content_parts = []
            
            # Специфичная логика для AIG Journal - собираем контент из определенных контейнеров
            lead_container = soup.find('div', class_='c-typography-lead')
            text_container = soup.find('div', class_='c-typography-text')
            
            # Добавляем вводный текст (lead)
            if lead_container:
                lead_text = lead_container.get_text(strip=True)
                if lead_text and len(lead_text) > 20:
                    content_parts.append(lead_text)
            
            # Добавляем основной текст
            if text_container:
                # Ищем все параграфы в основном контейнере
                paragraphs = text_container.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if (text and len(text) > 20 and 
                        not any(skip_word in text.lower() for skip_word in 
                               ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться', 'читать далее', 'подробнее'])):
                        content_parts.append(text)
            
            # Если специфичные контейнеры не найдены, используем общие селекторы
            if not content_parts:
                general_selectors = [
                    {'tag': 'div', 'class': 'article-text'},
                    {'tag': 'div', 'class': 'article-content'},
                    {'tag': 'div', 'class': 'content-text'},
                    {'tag': 'div', 'class': 'post-content'},
                    {'tag': 'div', 'class': 'entry-content'},
                    {'tag': 'article'},
                    {'tag': 'main'},
                ]
                
                for selector in general_selectors:
                    if 'class' in selector:
                        container = soup.find(selector['tag'], class_=selector['class'])
                    else:
                        container = soup.find(selector['tag'])
                        
                    if container:
                        # Ищем все параграфы и div с текстом внутри контейнера
                        text_elements = container.find_all(['p', 'div'], recursive=True)
                        for elem in text_elements:
                            # Пропускаем элементы с определенными классами
                            if elem.get('class'):
                                classes = ' '.join(elem.get('class', []))
                                if any(skip_class in classes.lower() for skip_class in 
                                      ['nav', 'menu', 'sidebar', 'footer', 'header', 'ad', 'banner', 'social', 'btn', 'button']):
                                    continue
                            
                            text = elem.get_text(strip=True)
                            if (text and len(text) > 20 and 
                                not any(skip_word in text.lower() for skip_word in 
                                       ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться', 'читать далее', 'подробнее'])):
                                content_parts.append(text)
                        
                        if content_parts:
                            break
            
            # Если основной метод не сработал, ищем все параграфы на странице
            if not content_parts:
                all_paragraphs = soup.find_all('p')
                for p in all_paragraphs:
                    text = p.get_text(strip=True)
                    if (text and len(text) > 20 and 
                        not any(skip_word in text.lower() for skip_word in 
                               ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться', 'читать далее'])):
                        content_parts.append(text)
            
            # Если все еще нет контента, ищем в любых div с текстом
            if not content_parts:
                all_divs = soup.find_all('div')
                for div in all_divs:
                    text = div.get_text(strip=True)
                    if (text and len(text) > 50 and len(text) < 1000 and
                        not any(skip_word in text.lower() for skip_word in 
                               ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться'])):
                        content_parts.append(text)
            
            # Убираем дубли и объединяем
            unique_parts = []
            seen_texts = set()
            for part in content_parts:
                if part not in seen_texts and len(part) > 20:
                    unique_parts.append(part)
                    seen_texts.add(part)
            
            return '\n\n'.join(unique_parts[:8])  # Ограничиваем количество абзацев
            
        except Exception as e:
            logger.error(f"Error extracting content from soup: {e}")
            return ""

    async def _fetch_full_article_with_metadata(self, url: str) -> tuple[str, Optional[datetime], Optional[str], Optional[int], Optional[str]]:
        """Получение полного контента статьи с метаданными"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch article {url}: {response.status}")
                    return "", None, None, None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Извлекаем метаданные
                published_date, published_time, views_count, author = await self._extract_article_metadata(soup)
                
                # Получаем контент из уже загруженного HTML
                content = await self._extract_content_from_soup(soup)
                
                return content, published_date, published_time, views_count, author
                
        except Exception as e:
            logger.error(f"Error fetching article with metadata {url}: {e}")
            return "", None, None, None, None
    
    async def _extract_article_metadata(self, soup: BeautifulSoup) -> tuple[Optional[datetime], Optional[str], Optional[int], Optional[str]]:
        """Извлечение метаданных статьи: дата, время, просмотры"""
        published_date = None
        published_time = None
        views_count = None
        author = None
        
        try:
            # Ищем дату публикации в различных местах
            date_selectors = [
                # Специфичный селектор для AIG Journal (приоритет)
                'div.date span',
                '.date span',
                # JSON-LD структурированные данные
                'script[type="application/ld+json"]',
                # Meta теги
                'meta[property="article:published_time"]',
                'meta[name="article:published_time"]',
                'meta[property="og:published_time"]',
                'meta[name="published_time"]',
                'meta[name="date"]',
                'meta[property="article:modified_time"]',
                # Time элементы
                'time[datetime]',
                'time[pubdate]',
                'time.published',
                'time.date',
                # Специфичные классы для AIG Journal
                '.date',
                '.published-date',
                '.article-date',
                '.post-date',
                '.entry-date',
                '.publication-date',
                # Общие селекторы
                '.c-typography-date',
                '.ui.label.date',
                'span[data-date]',
                'div[data-date]'
            ]
            
            for selector in date_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    date_str = None
                    
                    if elem.name == 'script':
                        # JSON-LD данные
                        try:
                            import json
                            json_data = json.loads(elem.string or '{}')
                            if isinstance(json_data, list):
                                json_data = json_data[0] if json_data else {}
                            date_str = (json_data.get('datePublished') or 
                                       json_data.get('dateCreated') or
                                       json_data.get('dateModified'))
                        except:
                            continue
                    elif elem.name == 'meta':
                        date_str = elem.get('content')
                    elif elem.name == 'time':
                        date_str = elem.get('datetime') or elem.get_text(strip=True)
                    else:
                        date_str = elem.get_text(strip=True)
                        # Также проверяем data-атрибуты
                        if not date_str:
                            date_str = elem.get('data-date') or elem.get('data-time')
                    
                    if date_str:
                        published_date = self._parse_date(date_str)
                        if published_date:
                            break
                
                if published_date:
                    break
            
            # Если дата не найдена, ищем в тексте страницы
            if not published_date:
                # Ищем паттерны дат в тексте
                text_content = soup.get_text()
                
                # Русские паттерны дат
                date_patterns = [
                    r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # dd.mm.yyyy - приоритет для AIG
                    r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})',
                    r'(\d{4})-(\d{1,2})-(\d{1,2})',
                    r'(\d{1,2})/(\d{1,2})/(\d{4})'
                ]
                
                for pattern in date_patterns:
                    matches = re.findall(pattern, text_content)
                    if matches:
                        try:
                            match = matches[0]
                            if len(match) == 3:
                                if isinstance(match[1], str) and match[1] in ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']:
                                    # Русский формат
                                    months = {
                                        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
                                        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
                                        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
                                    }
                                    day, month_name, year = match
                                    month = months[month_name]
                                    published_date = datetime(int(year), month, int(day))
                                elif pattern == r'(\d{1,2})\.(\d{1,2})\.(\d{4})':
                                    # Формат dd.mm.yyyy (специально для AIG)
                                    day, month, year = match
                                    published_date = datetime(int(year), int(month), int(day))
                                elif pattern.startswith(r'(\d{4})'):
                                    # Формат yyyy-mm-dd
                                    year, month, day = match
                                    published_date = datetime(int(year), int(month), int(day))
                                else:
                                    # Другие числовые форматы (dd/mm/yyyy)
                                    day, month, year = match
                                    published_date = datetime(int(year), int(month), int(day))
                                
                                if published_date:
                                    break
                        except Exception as parse_error:
                            logger.debug(f"Failed to parse date {match}: {parse_error}")
                            continue
            
            # Ищем время публикации
            time_elem = soup.find('time')
            if time_elem:
                time_str = time_elem.get('datetime') or time_elem.get_text(strip=True)
                if time_str and ':' in time_str:
                    published_time = time_str
            
            # Ищем количество просмотров
            views_selectors = [
                'span.views',
                'div.views',
                'span.view-count',
                'div.view-count',
                'span[data-views]',
                'div[data-views]'
            ]
            
            for selector in views_selectors:
                elem = soup.select_one(selector)
                if elem:
                    views_text = elem.get_text(strip=True) or elem.get('data-views', '')
                    views_match = re.search(r'(\d+)', views_text)
                    if views_match:
                        views_count = int(views_match.group(1))
                        break
                        
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
        
            # Ищем автора
            author_selectors = [
                'meta[name="author"]',
                'meta[property="article:author"]',
                '.author',
                '.byline',
                '.author-name',
                '[rel="author"]',
                '.post-author'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    if author_elem.name == 'meta':
                        author = author_elem.get('content', '').strip()
                    else:
                        author = author_elem.get_text(strip=True)
                    if author:
                        break
        
        return published_date, published_time, views_count, author