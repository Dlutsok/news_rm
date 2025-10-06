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

class RiaParser(BaseNewsParser):
    """Парсер для ria.ru (раздел здоровье)"""
    
    def __init__(self):
        super().__init__("ria", "https://ria.ru")
        self.name = "ria"  # Добавляем атрибут name
        self.news_url = "https://ria.ru/health/"
    
    async def parse_news_list(self, max_articles: int = 10, date_filter: Optional[str] = None, fetch_full_content: bool = True) -> List[NewsSource]:
        """Парсинг списка новостей с раздела здоровье ria.ru с поддержкой AJAX пагинации"""
        try:
            news_items = []
            seen_urls = set()
            seen_titles = set()
            current_url = self.news_url
            page_num = 1
            
            while len(news_items) < max_articles:
                logger.info(f"Parsing RIA page {page_num}, current articles: {len(news_items)}")
                
                # Запрашиваем страницу
                async with self.session.get(current_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch news list from {current_url}: {response.status}")
                        break
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем элементы новостей по структуре РИА
                    news_containers = soup.find_all('div', class_='list-item__content')
                    
                    if not news_containers:
                        logger.info(f"No news containers found on page {page_num}")
                        break
                    
                    logger.info(f"Found {len(news_containers)} news containers on page {page_num}")
                    
                    # Парсим новости на текущей странице
                    page_added = 0
                    for container in news_containers:
                        try:
                            # Проверяем лимит
                            if len(news_items) >= max_articles:
                                break
                            
                            # Ищем ссылку на статью
                            title_link = container.find('a', class_='list-item__title')
                            if not title_link:
                                continue
                                
                            href = title_link.get('href')
                            if not href:
                                continue
                                
                            # Формируем полную ссылку
                            if href.startswith('/'):
                                full_url = urljoin(self.base_url, href)
                            else:
                                full_url = href
                            
                            # Проверяем на дубли по URL
                            if full_url in seen_urls:
                                continue
                            seen_urls.add(full_url)
                            
                            # Извлекаем заголовок
                            title = title_link.get_text(strip=True)
                            if not title:
                                continue
                                
                            # Проверяем на дубли по заголовку
                            if title in seen_titles:
                                continue
                            seen_titles.add(title)
                            
                            # Извлекаем изображение (если есть)
                            image_link = container.find('a', class_='list-item__image')
                            image_url = None
                            if image_link:
                                img_tag = image_link.find('img')
                                if img_tag:
                                    image_url = img_tag.get('src')
                            
                            # Если нужен полный контент, парсим статью с метаданными
                            full_content = ""
                            published_date = None
                            published_time = None
                            views_count = None
                            author = None
                            
                            if fetch_full_content:
                                full_content, published_date, published_time, views_count, author = await self._fetch_full_article_with_metadata(full_url)
                            
                            # Используем заголовок как краткое содержание если нет полного контента
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
                                source_site="ria.ru"
                            )
                            
                            if self._is_relevant_news(news_item, date_filter):
                                news_items.append(news_item)
                                page_added += 1
                                logger.info(f"Added news {len(news_items)}: {title[:50]}...")
                                
                                # Добавляем задержку между запросами
                                await asyncio.sleep(0.5)
                                
                        except Exception as e:
                            logger.warning(f"Error parsing article container: {e}")
                            continue
                    
                    logger.info(f"Added {page_added} articles from page {page_num}")
                    
                    # Если достигли лимита, выходим
                    if len(news_items) >= max_articles:
                        break
                    
                    # Ищем ссылку на следующую страницу (кнопка "Еще" или data-next-url)
                    data_url = None
                    
                    # Сначала ищем кнопку "Еще"
                    more_button = soup.find('div', class_='list-more')
                    if more_button:
                        data_url = more_button.get('data-url')
                        logger.info("Found 'more' button with data-url")
                    
                    # Если кнопки нет, ищем data-next-url в контейнере
                    if not data_url:
                        next_url_container = soup.find(attrs={'data-next-url': True})
                        if next_url_container:
                            data_url = next_url_container.get('data-next-url')
                            logger.info("Found data-next-url in container")
                    
                    if not data_url:
                        logger.info("No pagination URL found, stopping pagination")
                        break
                    
                    # Формируем URL следующей страницы
                    if data_url.startswith('/'):
                        current_url = urljoin(self.base_url, data_url)
                    else:
                        current_url = data_url
                    
                    logger.info(f"Next page URL: {current_url}")
                    page_num += 1
                    
                    # Добавляем задержку между страницами
                    await asyncio.sleep(1.0)
            
            logger.info(f"Successfully parsed {len(news_items)} unique news articles from RIA (pages: {page_num})")
            return news_items
                
        except Exception as e:
            logger.error(f"Error parsing RIA news list: {e}")
            return []
    
    async def _fetch_full_article(self, url: str) -> str:
        """Получение полного контента статьи с ria.ru"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch article {url}: {response.status}")
                    return ""
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Удаляем ненужные элементы
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                    element.decompose()
                
                # Ищем основной контент статьи РИА
                content_parts = []
                
                # Основные селекторы для контента РИА
                content_selectors = [
                    'div.article__body',
                    'div.article__text', 
                    'div.article-text',
                    'div[data-type="text"]',
                    '.article__content',
                    '.article-body',
                    '.article__block[data-type="text"]'
                ]
                
                # Используем set для избежания дублирования
                seen_texts = set()
                
                for selector in content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        for elem in elements:
                            # Ищем все параграфы внутри элемента
                            paragraphs = elem.find_all(['p', 'div'], recursive=True)
                            if paragraphs:
                                for p in paragraphs:
                                    text = p.get_text(strip=True)
                                    if text and len(text) > 20 and text not in seen_texts:  # Проверяем дубли
                                        content_parts.append(text)
                                        seen_texts.add(text)
                            else:
                                # Если нет параграфов, берем весь текст элемента
                                text = elem.get_text(strip=True)
                                if text and len(text) > 50 and text not in seen_texts:
                                    content_parts.append(text)
                                    seen_texts.add(text)
                        if content_parts:
                            break
                
                # Если основные селекторы не сработали, ищем все параграфы в статье
                if not content_parts:
                    # Ищем в основном контейнере статьи
                    main_containers = soup.find_all(['article', 'main', '.content', '.post-content'])
                    for container in main_containers:
                        if container:
                            paragraphs = container.find_all('p')
                            for p in paragraphs:
                                text = p.get_text(strip=True)
                                if text and len(text) > 20 and text not in seen_texts:
                                    content_parts.append(text)
                                    seen_texts.add(text)
                            if content_parts:
                                break
                
                # Если все еще нет контента, ищем любые параграфы на странице
                if not content_parts:
                    all_paragraphs = soup.find_all('p')
                    for p in all_paragraphs:
                        text = p.get_text(strip=True)
                        # Фильтруем навигацию, рекламу и короткие тексты, а также дубли
                        if (text and len(text) > 30 and text not in seen_texts and
                            not any(skip_word in text.lower() for skip_word in 
                                   ['навигация', 'реклама', 'подписаться', 'следить', 'комментарий', 'поделиться'])):
                            content_parts.append(text)
                            seen_texts.add(text)
                
                # Объединяем контент с правильными разделителями
                full_content = '\n\n'.join(content_parts)
                
                # Очищаем лишние пробелы, но сохраняем структуру
                full_content = re.sub(r'[ \t]+', ' ', full_content)  # Убираем лишние пробелы и табы
                full_content = re.sub(r'\n{3,}', '\n\n', full_content)  # Ограничиваем количество переносов строк
                full_content = full_content.strip()
                
                # Ограничиваем длину контента
                if len(full_content) > 8000:
                    # Обрезаем по последнему полному предложению
                    truncated = full_content[:8000]
                    last_sentence = truncated.rfind('.')
                    if last_sentence > 6000:  # Если есть предложение в разумных пределах
                        full_content = truncated[:last_sentence + 1] + "\n\n[Текст сокращен...]"
                    else:
                        full_content = truncated + "..."
                
                return full_content
                
        except Exception as e:
            logger.error(f"Error fetching full article {url}: {e}")
            return ""
    
    async def _extract_article_metadata(self, soup: BeautifulSoup) -> tuple[Optional[datetime], Optional[str], Optional[int], Optional[str]]:
        """Извлечение метаданных статьи РИА: дата, время, просмотры, автор"""
        published_date = None
        published_time = None
        views_count = None
        author = None
        
        try:
            # Ищем дату и время в мета-тегах
            date_meta = soup.find('meta', {'property': 'article:published_time'}) or \
                       soup.find('meta', {'name': 'mediator_published_time'})
            
            if date_meta:
                date_content = date_meta.get('content')
                if date_content:
                    try:
                        # Парсим ISO формат даты
                        dt = datetime.fromisoformat(date_content.replace('Z', '+00:00'))
                        published_date = dt
                        published_time = dt.strftime('%H:%M')
                    except Exception as e:
                        logger.warning(f"Error parsing date: {e}")
                        pass
            
            # Альтернативный поиск даты в тексте
            if not published_date:
                # Ищем дату в заголовке или подзаголовке
                date_patterns = [
                    r'(\d{1,2}\s+\w+\s+\d{4})',  # "30 июля 2025"
                    r'(\d{1,2}\.\d{1,2}\.\d{4})',  # "30.07.2025"
                    r'(\d{4}-\d{1,2}-\d{1,2})'   # "2025-07-30"
                ]
                
                page_text = soup.get_text()
                for pattern in date_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        date_str = match.group(1)
                        parsed_date = self._parse_date(date_str)
                        if parsed_date:
                            published_date = parsed_date
                            break
            
            # Ищем автора
            author_selectors = [
                'meta[name="mediator_author"]',
                'meta[property="article:author"]',
                '.article__author',
                '.author-name',
                '[data-type="author"]'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    if author_elem.name == 'meta':
                        author = author_elem.get('content')
                    else:
                        author = author_elem.get_text(strip=True)
                    if author:
                        break
            
            # Просмотры обычно загружаются динамически на РИА, поэтому оставляем None
            
        except Exception as e:
            logger.warning(f"Error extracting RIA metadata: {e}")
        
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
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                    element.decompose()
                
                # Ищем основной контент статьи РИА
                content_parts = []
                
                # Основные селекторы для контента РИА
                content_selectors = [
                    'div.article__body',
                    'div.article__text',
                    'div.article-text',
                    'div[data-type="text"]',
                    '.article__content p',
                    '.article-body p'
                ]
                
                for selector in content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        for elem in elements:
                            text = elem.get_text(strip=True)
                            if text and len(text) > 30:  # Фильтруем короткие строки
                                content_parts.append(text)
                        if content_parts:
                            break
                
                # Если основные селекторы не сработали, ищем параграфы в статье
                if not content_parts:
                    article_container = soup.find('article') or soup.find('main')
                    if article_container:
                        paragraphs = article_container.find_all('p')
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            if text and len(text) > 30:
                                content_parts.append(text)
                
                # Объединяем контент
                full_content = ' '.join(content_parts)
                
                # Очищаем и ограничиваем длину
                full_content = re.sub(r'\s+', ' ', full_content).strip()
                
                # Ограничиваем длину контента
                if len(full_content) > 6000:
                    full_content = full_content[:6000] + "..."
                
                return full_content, published_date, published_time, views_count, author
                
        except Exception as e:
            logger.error(f"Error fetching full article {url}: {e}")
            return "", None, None, None, None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Парсинг даты из строки с поддержкой русских месяцев"""
        if not date_str:
            return None
            
        # Русские месяцы для РИА
        russian_months = {
            'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
            'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
            'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12',
            'янв': '01', 'фев': '02', 'мар': '03', 'апр': '04',
            'май': '05', 'июн': '06', 'июл': '07', 'авг': '08',
            'сен': '09', 'окт': '10', 'ноя': '11', 'дек': '12'
        }
        
        # Заменяем русские месяцы на числа
        date_str_lower = date_str.lower()
        for ru_month, month_num in russian_months.items():
            if ru_month in date_str_lower:
                date_str = re.sub(ru_month, month_num, date_str_lower)
                break
        
        # Форматы дат для РИА
        date_formats = [
            "%d %m %Y",      # "30 07 2025"
            "%d.%m.%Y",      # "30.07.2025"
            "%Y-%m-%d",      # "2025-07-30"
            "%d/%m/%Y"       # "30/07/2025"
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str.strip(), date_format)
            except ValueError:
                continue
                
        logger.warning(f"Could not parse RIA date: {date_str}")
        return None
    
    async def parse_news_list_with_batch_save(self, max_articles: int = 10, date_filter: Optional[str] = None, 
                                            fetch_full_content: bool = True, batch_size: int = 10, 
                                            save_callback=None) -> List[NewsSource]:
        """Парсинг списка новостей с промежуточным сохранением пакетами"""
        try:
            news_items = []
            batch_buffer = []
            seen_urls = set()
            seen_titles = set()
            current_url = self.news_url
            page_num = 1
            total_saved = 0
            
            while len(news_items) < max_articles:
                logger.info(f"Parsing RIA page {page_num}, current articles: {len(news_items)}")
                
                # Запрашиваем страницу
                async with self.session.get(current_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch news list from {current_url}: {response.status}")
                        break
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем элементы новостей по структуре РИА
                    news_containers = soup.find_all('div', class_='list-item__content')
                    
                    if not news_containers:
                        logger.info(f"No news containers found on page {page_num}")
                        break
                    
                    logger.info(f"Found {len(news_containers)} news containers on page {page_num}")
                    page_added = 0
                    
                    for container in news_containers:
                        if len(news_items) >= max_articles:
                            break
                            
                        try:
                            # Извлекаем ссылку на статью
                            title_link = container.find('a', class_='list-item__title')
                            if not title_link:
                                continue
                            
                            article_url = title_link.get('href')
                            if not article_url:
                                continue
                            
                            # Делаем абсолютный URL
                            full_url = urljoin(self.base_url, article_url)
                            
                            # Проверяем на дубли по URL
                            if full_url in seen_urls:
                                continue
                            seen_urls.add(full_url)
                            
                            # Извлекаем заголовок
                            title = title_link.get_text(strip=True)
                            if not title:
                                continue
                                
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
                            
                            # Используем заголовок как краткое содержание если нет полного контента
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
                                source_site="ria.ru"
                            )
                            
                            if self._is_relevant_news(news_item, date_filter):
                                news_items.append(news_item)
                                batch_buffer.append(news_item)
                                page_added += 1
                                logger.info(f"Added news {len(news_items)}: {title[:50]}...")
                                
                                # Проверяем, нужно ли сохранить пакет
                                if len(batch_buffer) >= batch_size and save_callback:
                                    logger.info(f"🔄 Сохраняем пакет из {len(batch_buffer)} статей...")
                                    saved_count = await save_callback(batch_buffer.copy())
                                    total_saved += saved_count
                                    logger.info(f"✅ Сохранено {saved_count} статей. Всего сохранено: {total_saved}")
                                    batch_buffer.clear()
                                
                                # Добавляем задержку между запросами
                                await asyncio.sleep(0.5)
                                
                        except Exception as e:
                            logger.warning(f"Error parsing article container: {e}")
                            continue
                    
                    logger.info(f"Added {page_added} articles from page {page_num}")
                    
                    # Если достигли лимита, выходим
                    if len(news_items) >= max_articles:
                        break
                    
                    # Ищем ссылку на следующую страницу (кнопка "Еще" или data-next-url)
                    data_url = None
                    
                    # Сначала ищем кнопку "Еще"
                    more_button = soup.find('div', class_='list-more')
                    if more_button:
                        data_url = more_button.get('data-url')
                        logger.info("Found 'more' button with data-url")
                    
                    # Если кнопки нет, ищем data-next-url в контейнере
                    if not data_url:
                        next_container = soup.find('div', {'data-next-url': True})
                        if next_container:
                            data_url = next_container.get('data-next-url')
                            logger.info("Found data-next-url in container")
                    
                    # Если нет data-url, пробуем найти стандартную пагинацию
                    if not data_url:
                        pagination_links = soup.find_all('a', class_='pagination__item')
                        for link in pagination_links:
                            if 'Далее' in link.get_text() or 'next' in link.get('class', []):
                                data_url = link.get('href')
                                break
                    
                    if data_url:
                        # Формируем URL для следующей страницы
                        if data_url.startswith('/'):
                            current_url = urljoin(self.base_url, data_url)
                        elif data_url.startswith('http'):
                            current_url = data_url
                        else:
                            current_url = urljoin(current_url, data_url)
                        
                        logger.info(f"Moving to next page: {current_url}")
                        page_num += 1
                        
                        # Добавляем задержку между страницами
                        await asyncio.sleep(1)
                    else:
                        logger.info("No more pages found")
                        break
            
            # Сохраняем оставшиеся статьи в буфере
            if batch_buffer and save_callback:
                logger.info(f"🔄 Сохраняем последний пакет из {len(batch_buffer)} статей...")
                saved_count = await save_callback(batch_buffer.copy())
                total_saved += saved_count
                logger.info(f"✅ Сохранено {saved_count} статей. Итого сохранено: {total_saved}")
            
            logger.info(f"Parsing completed. Total articles: {len(news_items)}, Total saved: {total_saved}")
            return news_items
            
        except Exception as e:
            logger.error(f"Error in parse_news_list_with_batch_save: {e}")
            return []