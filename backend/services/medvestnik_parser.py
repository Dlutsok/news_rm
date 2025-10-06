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

class MedvestnikParser(BaseNewsParser):
    """Парсер для medvestnik.ru"""
    
    def __init__(self):
        super().__init__("medvestnik", "https://medvestnik.ru")
        self.name = "medvestnik"  # Добавляем атрибут name
        self.news_url = "https://medvestnik.ru/content/roubric/news"
    
    async def parse_news_list(self, max_articles: int = 10, date_filter: Optional[str] = None, fetch_full_content: bool = True) -> List[NewsSource]:
        """Парсинг списка новостей с главной страницы medvestnik.ru с поддержкой пагинации"""
        try:
            logger.info(f"Starting parse_news_list for medvestnik with max_articles={max_articles}")
            logger.info(f"Session status: {self.session is not None and not getattr(self.session, 'closed', True)}")
            
            if not self.session or getattr(self.session, 'closed', True):
                logger.error("Session is not initialized or closed")
                return []
            
            news_items = []
            seen_urls = set()
            seen_titles = set()
            page = 1
            
            while len(news_items) < max_articles:
                # Формируем URL для текущей страницы
                page_url = f"{self.news_url}?page={page}" if page > 1 else self.news_url
                logger.info(f"Парсинг страницы {page}: {page_url}")
                
                async with self.session.get(page_url) as response:
                    logger.info(f"HTTP response status: {response.status}")
                    if response.status != 200:
                        logger.error(f"Failed to fetch news list: {response.status}")
                        break
                    
                    html = await response.text()
                    logger.info(f"Received HTML content length: {len(html)}")
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем ссылки на статьи с правильным селектором для medvestnik.ru
                    article_links = soup.find_all('a', {'class': 'ui', 'href': re.compile(r'/content/news/')})
                    
                    logger.info(f"Found {len(article_links)} news article links on page {page}")
                    
                    if not article_links:
                        logger.info("No more articles found, stopping pagination")
                        break
                    
                    page_articles_added = 0
                
                    for link in article_links:
                        try:
                            # Проверяем лимит статей
                            if len(news_items) >= max_articles:
                                break
                                
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
                            
                            # Извлекаем заголовок из превью - пробуем разные варианты
                            title_elem = (
                                link.find('h3', class_='ui header no-marged') or
                                link.find('h3') or
                                link.find('h2') or
                                link.find('h1') or
                                link.find(class_='title') or
                                link.find(class_='header')
                            )
                            
                            # Если заголовок не найден в ссылке, пробуем найти в родительском элементе
                            if not title_elem:
                                parent = link.parent
                                if parent:
                                    title_elem = (
                                        parent.find('h3', class_='ui header no-marged') or
                                        parent.find('h3') or
                                        parent.find('h2') or
                                        parent.find('h1')
                                    )
                            
                            title = title_elem.get_text(strip=True) if title_elem else f"Статья {len(news_items) + 1}"
                            
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
                            author = None
                            
                            if fetch_full_content:
                                full_content, published_date, published_time, views_count, author = await self._fetch_full_article_with_metadata(full_url)
                            
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
                                author=author,
                                source_site="medvestnik.ru"
                            )
                            
                            if self._is_relevant_news(news_item, date_filter):
                                news_items.append(news_item)
                                page_articles_added += 1
                                logger.info(f"Added news: {title[:50]}...")
                                
                                # Добавляем задержку между запросами
                                await asyncio.sleep(0.5)
                                    
                        except Exception as e:
                            logger.warning(f"Error parsing article link: {e}")
                            continue
                    
                    logger.info(f"Page {page}: added {page_articles_added} articles, total: {len(news_items)}")
                    
                    # Если на странице не добавили ни одной новой статьи, прекращаем
                    if page_articles_added == 0:
                        logger.info("No new articles added on this page, stopping pagination")
                        break
                    
                    # Переходим к следующей странице
                    page += 1
                    
                    # Добавляем задержку между страницами
                    await asyncio.sleep(1)
            
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
                
                # Основные селекторы для контента Medvestnik
                content_selectors = [
                    'div.ui.container',
                    'div.article-content',
                    'div.post-content', 
                    'div.entry-content',
                    'article',
                    'main',
                    'div.content'
                ]
                
                for selector in content_selectors:
                    container = soup.find('div', class_=selector.replace('div.', '').replace('.', '')) if 'div.' in selector else soup.find(selector)
                    if container:
                        # Ищем все параграфы и div с текстом внутри контейнера
                        text_elements = container.find_all(['p', 'div'], recursive=True)
                        for elem in text_elements:
                            # Пропускаем элементы с определенными классами (навигация, реклама и т.д.)
                            if elem.get('class'):
                                classes = ' '.join(elem.get('class', []))
                                if any(skip_class in classes.lower() for skip_class in 
                                      ['nav', 'menu', 'sidebar', 'footer', 'header', 'ad', 'banner', 'social']):
                                    continue
                            
                            text = elem.get_text(strip=True)
                            if (text and len(text) > 30 and 
                                not any(skip_word in text.lower() for skip_word in 
                                       ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться', 'читать далее'])):
                                content_parts.append(text)
                        
                        if content_parts:
                            break
                
                # Если основной метод не сработал, ищем все параграфы на странице
                if not content_parts:
                    all_paragraphs = soup.find_all('p')
                    for p in all_paragraphs:
                        text = p.get_text(strip=True)
                        if (text and len(text) > 30 and 
                            not any(skip_word in text.lower() for skip_word in 
                                   ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться'])):
                            content_parts.append(text)
                
                # Объединяем контент с правильными разделителями
                full_content = '\n\n'.join(content_parts)
                
                # Очищаем лишние пробелы, но сохраняем структуру
                full_content = re.sub(r'[ \t]+', ' ', full_content)  # Убираем лишние пробелы и табы
                full_content = re.sub(r'\n{3,}', '\n\n', full_content)  # Ограничиваем количество переносов строк
                full_content = full_content.strip()
                
                # Ограничиваем длину контента
                if len(full_content) > 6000:
                    # Обрезаем по последнему полному предложению
                    truncated = full_content[:6000]
                    last_sentence = truncated.rfind('.')
                    if last_sentence > 4000:  # Если есть предложение в разумных пределах
                        full_content = truncated[:last_sentence + 1] + "\n\n[Текст сокращен...]"
                    else:
                        full_content = truncated + "..."
                
                return full_content
                
        except Exception as e:
            logger.error(f"Error fetching full article {url}: {e}")
            return ""
    
    async def _extract_article_metadata(self, soup: BeautifulSoup) -> tuple[Optional[datetime], Optional[str], Optional[int], Optional[str]]:
        """Извлечение метаданных статьи: дата, время, просмотры"""
        published_date = None
        published_time = None
        views_count = None
        author = None
        
        try:
            # Ищем блок с метаданными
            metadata_block = soup.find('div', class_='ui list muted horizontal spaced-bottom-quorter middle aligned')
            
            if metadata_block:
                items = metadata_block.find_all('div', class_='item')
                
                for item in items:
                    # Ищем иконку календаря для даты
                    calendar_icon = item.find('i', class_='calendar icon')
                    if calendar_icon:
                        date_text = item.get_text(strip=True)
                        published_date = self._parse_date(date_text)
                        continue
                    
                    # Ищем иконку часов для времени
                    clock_icon = item.find('i', class_='clock icon')
                    if clock_icon:
                        published_time = item.get_text(strip=True)
                        continue
                    
                    # Ищем иконку глаза для просмотров
                    eye_icon = item.find('i', class_='eye icon')
                    if eye_icon:
                        views_text = item.get_text(strip=True)
                        # Извлекаем число из текста
                        views_match = re.search(r'\d+', views_text)
                        if views_match:
                            views_count = int(views_match.group())
                        continue
                    
                    # Альтернативный поиск по классам
                    views_counter = item.find(class_='c-views-counter')
                    if views_counter:
                        views_text = views_counter.get_text(strip=True)
                        views_match = re.search(r'\d+', views_text)
                        if views_match:
                            views_count = int(views_match.group())
                        continue
                    
                    # Поиск текстовых элементов с датой/временем
                    text_elem = item.find(class_='text')
                    if text_elem:
                        text_content = text_elem.get_text(strip=True)
                        # Проверяем, похоже ли на дату
                        if re.match(r'\d{1,2}\.\d{1,2}\.\d{4}', text_content):
                            published_date = self._parse_date(text_content)
                        # Проверяем, похоже ли на время
                        elif re.match(r'\d{1,2}:\d{2}', text_content):
                            published_time = text_content
                            
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
                        
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
        
        return published_date, published_time, views_count, author
    
    async def _fetch_full_article_with_metadata(self, url: str) -> tuple[str, Optional[datetime], Optional[str], Optional[int], Optional[str]]:
        """Получение полного контента статьи вместе с метаданными"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch article {url}: {response.status}")
                    return "", None, None, None, None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Извлекаем метаданные
                published_date, published_time, views_count, author = await self._extract_article_metadata(soup)
                
                # Удаляем ненужные элементы
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()
                
                # Ищем основной контент статьи
                content_parts = []
                
                # Основные селекторы для контента Medvestnik
                content_selectors = [
                    'div.ui.container',
                    'div.article-content',
                    'div.post-content', 
                    'div.entry-content',
                    'article',
                    'main',
                    'div.content'
                ]
                
                for selector in content_selectors:
                    container = soup.find('div', class_=selector.replace('div.', '').replace('.', '')) if 'div.' in selector else soup.find(selector)
                    if container:
                        # Ищем все параграфы и div с текстом внутри контейнера
                        text_elements = container.find_all(['p', 'div'], recursive=True)
                        for elem in text_elements:
                            # Пропускаем элементы с определенными классами (навигация, реклама и т.д.)
                            if elem.get('class'):
                                classes = ' '.join(elem.get('class', []))
                                if any(skip_class in classes.lower() for skip_class in 
                                      ['nav', 'menu', 'sidebar', 'footer', 'header', 'ad', 'banner', 'social']):
                                    continue
                            
                            text = elem.get_text(strip=True)
                            if (text and len(text) > 30 and 
                                not any(skip_word in text.lower() for skip_word in 
                                       ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться', 'читать далее'])):
                                content_parts.append(text)
                        
                        if content_parts:
                            break
                
                # Если основной метод не сработал, ищем все параграфы на странице
                if not content_parts:
                    all_paragraphs = soup.find_all('p')
                    for p in all_paragraphs:
                        text = p.get_text(strip=True)
                        if (text and len(text) > 30 and 
                            not any(skip_word in text.lower() for skip_word in 
                                   ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться'])):
                            content_parts.append(text)
                
                # Объединяем контент с правильными разделителями
                full_content = '\n\n'.join(content_parts)
                
                # Очищаем лишние пробелы, но сохраняем структуру
                full_content = re.sub(r'[ \t]+', ' ', full_content)  # Убираем лишние пробелы и табы
                full_content = re.sub(r'\n{3,}', '\n\n', full_content)  # Ограничиваем количество переносов строк
                full_content = full_content.strip()
                
                # Ограничиваем длину контента
                if len(full_content) > 6000:
                    # Обрезаем по последнему полному предложению
                    truncated = full_content[:6000]
                    last_sentence = truncated.rfind('.')
                    if last_sentence > 4000:  # Если есть предложение в разумных пределах
                        full_content = truncated[:last_sentence + 1] + "\n\n[Текст сокращен...]"
                    else:
                        full_content = truncated + "..."
                
                return full_content, published_date, published_time, views_count, author
                
        except Exception as e:
            logger.error(f"Error fetching full article {url}: {e}")
            return "", None, None, None, None