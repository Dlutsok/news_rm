"""
РБК медицинские новости парсер
Парсит новости с тега health: https://www.rbc.ru/life/tag/health
"""

import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging

from models.schemas import NewsSource
from services.base_parser import BaseNewsParser

logger = logging.getLogger(__name__)

class RBCMedicalParser(BaseNewsParser):
    """
    Парсер медицинских новостей с сайта РБК с тега health
    
    Парсит статьи напрямую с https://www.rbc.ru/life/tag/health
    Поддерживает пагинацию для получения большего количества статей
    """
    
    def __init__(self):
        super().__init__(source_name="rbc_medical", base_url="https://www.rbc.ru")
        self.tag_url = "https://www.rbc.ru/life/tag/health"
    
    async def parse_news_list(self, max_articles: int = 10, date_filter: Optional[str] = None, fetch_full_content: bool = True) -> List[NewsSource]:
        """Основной метод парсинга новостей с тега health"""
        articles = []
        
        try:
            logger.info(f"Начинаем парсинг РБК health новостей с {self.tag_url}, лимит: {max_articles}")
            
            page = 1
            processed_count = 0
            last_cursor = None
            
            while processed_count < max_articles:
                # Формируем URL с пагинацией
                if page == 1:
                    url = self.tag_url
                else:
                    url = f"{self.tag_url}?cursor={last_cursor}" if last_cursor else self.tag_url
                
                logger.info(f"Парсим страницу {page}: {url}")
                
                # Получаем HTML страницы
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                
                # Ищем JSON-данные в скрипте
                script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
                if not script_tag:
                    logger.error("Не найден скрипт с данными __NEXT_DATA__")
                    break
                
                try:
                    import json
                    json_data = json.loads(script_tag.string)
                    articles_data = json_data.get('props', {}).get('pageProps', {}).get('articles', {}).get('items', [])
                    
                    if not articles_data:
                        logger.warning(f"На странице {page} не найдено статей в JSON")
                        break
                    
                    logger.info(f"Найдено {len(articles_data)} статей на странице {page}")
                    
                    # Сохраняем cursor для следующей страницы
                    new_cursor = json_data.get('props', {}).get('pageProps', {}).get('articles', {}).get('endCursor')
                    logger.info(f"Cursor: {last_cursor} -> {new_cursor}")
                    last_cursor = new_cursor
                    
                    page_articles_count = 0
                    for article_data in articles_data:
                        if processed_count >= max_articles:
                            break
                        
                        try:
                            # Извлекаем данные из JSON
                            title = article_data.get('title', '').strip()
                            if not title:
                                continue
                            
                            # Формируем URL статьи
                            canonical_url = article_data.get('canonicalUrl', '')
                            if canonical_url.startswith('/'):
                                article_url = f"https://www.rbc.ru/life{canonical_url}"
                            else:
                                article_url = canonical_url
                            
                            # Все статьи на странице /life/tag/health уже медицинские
                            # Убираем дополнительную фильтрацию по тегам
                            
                            # Извлекаем дату публикации
                            published_date = None
                            publish_date_t = article_data.get('publishDateT')
                            if publish_date_t:
                                published_date = datetime.fromtimestamp(publish_date_t)
                            
                            # Проверяем фильтр по дате
                            if date_filter and published_date:
                                if not self._is_relevant_news(published_date, date_filter):
                                    logger.debug(f"Статья не прошла фильтр по дате: {title}")
                                    continue
                            
                            # Получаем контент
                            content = ""
                            if fetch_full_content:
                                full_content, article_published_date = await self._fetch_full_article(article_url)
                                if full_content:
                                    content = full_content
                                else:
                                    # Используем описание из JSON
                                    content = article_data.get('metaDescription', '').strip() or title
                                
                                # Если получили дату из статьи, используем её
                                if article_published_date:
                                    published_date = article_published_date
                                
                                # Добавляем задержку между запросами
                                await asyncio.sleep(0.5)
                            else:
                                # Используем описание из JSON
                                content = article_data.get('metaDescription', '').strip() or title
                            
                            # Создаем объект новости
                            news_item = NewsSource(
                                title=title,
                                url=article_url,
                                content=content,
                                published_date=published_date,
                                source_site="rbc.ru"
                            )
                            
                            articles.append(news_item)
                            processed_count += 1
                            page_articles_count += 1
                            logger.debug(f"Добавлена новость: {title}")
                            
                        except Exception as e:
                            logger.error(f"Ошибка при обработке статьи: {e}")
                            continue
                    
                    # Проверяем, есть ли еще страницы
                    more_exists = json_data.get('props', {}).get('pageProps', {}).get('articles', {}).get('moreExists', False)
                    if not more_exists or page_articles_count == 0:
                        logger.info("Достигнут конец списка статей")
                        break
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка при парсинге JSON: {e}")
                    break
                
                page += 1
                
                # Добавляем задержку между страницами
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Ошибка при парсинге РБК health: {e}")
        
        logger.info(f"Парсинг завершен. Получено {len(articles)} новостей")
        return articles
    
    async def _fetch_full_article(self, url: str) -> tuple[Optional[str], Optional[datetime]]:
        """Получение полного текста статьи и даты публикации"""
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                # Извлекаем дату публикации из метаданных статьи
                published_date = None
                metadata = self._extract_article_metadata(soup, url)
                if 'published_date' in metadata:
                    published_date = metadata['published_date']
                
                # Ищем основной контент статьи - сначала пробуем найти контейнер
                content_selectors = [
                    '.article__text',
                    '.article__content', 
                    '.news-text',
                    '.js-mediator-article',
                    '[data-vr-contentbox]',
                    '.article__text__overview'
                ]
                
                content_parts = []
                
                # Пробуем найти основной контейнер статьи
                main_container = None
                for selector in content_selectors:
                    container = soup.select_one(selector)
                    if container:
                        main_container = container
                        break
                
                if main_container:
                    # Убираем рекламные блоки и служебную информацию
                    for unwanted in main_container.find_all(['script', 'style', '.banner', '.adv', '.social', '.promo']):
                        unwanted.decompose()
                    
                    # Извлекаем параграфы из контейнера
                    paragraphs = main_container.find_all(['p', 'div'])
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text and len(text) > 30 and not any(skip in text.lower() for skip in ['реклама', 'подписаться', 'читайте также']):
                            content_parts.append(text)
                else:
                    # Если не нашли контейнер, ищем все параграфы на странице
                    paragraphs = soup.find_all('p')
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text and len(text) > 30 and not any(skip in text.lower() for skip in ['реклама', 'подписаться', 'читайте также']):
                            content_parts.append(text)
                
                content = '\n\n'.join(content_parts) if content_parts else None
                
                return content, published_date
                
        except Exception as e:
            logger.error(f"Ошибка при получении полного текста статьи {url}: {e}")
            return None, None
    
    def _extract_article_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """Извлечение метаданных статьи"""
        metadata = {}
        
        try:
            # Автор
            author_selectors = [
                'meta[name="author"]',
                '.article__author',
                '.author-name',
                '[data-vr-contentbox] .article__authors'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    if author_elem.name == 'meta':
                        metadata['author'] = author_elem.get('content', '').strip()
                    else:
                        metadata['author'] = author_elem.get_text(strip=True)
                    break
            
            # Дата публикации из meta тегов
            date_elem = soup.select_one('meta[property="article:published_time"]')
            if date_elem:
                date_content = date_elem.get('content')
                if date_content:
                    try:
                        metadata['published_date'] = datetime.fromisoformat(date_content.replace('Z', '+00:00'))
                    except:
                        pass
            
            # Если не нашли в meta, ищем в time элементах
            if 'published_date' not in metadata:
                time_elem = soup.select_one('time[datetime]')
                if time_elem:
                    datetime_attr = time_elem.get('datetime')
                    if datetime_attr:
                        try:
                            metadata['published_date'] = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        except:
                            pass
            
            # Теги/категории
            tags = []
            tag_selectors = [
                'meta[name="keywords"]',
                '.article__tags a',
                '.tags a'
            ]
            
            for selector in tag_selectors:
                tag_elems = soup.select(selector)
                for elem in tag_elems:
                    if elem.name == 'meta':
                        keywords = elem.get('content', '')
                        tags.extend([tag.strip() for tag in keywords.split(',') if tag.strip()])
                    else:
                        tag_text = elem.get_text(strip=True)
                        if tag_text:
                            tags.append(tag_text)
                
                if tags:
                    break
            
            if tags:
                metadata['tags'] = tags
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении метаданных: {e}")
        
        return metadata
    
    def _parse_rbc_date(self, date_str: str) -> Optional[datetime]:
        """Парсинг даты в различных форматах РБК"""
        if not date_str:
            return None
        
        try:
            # Убираем лишние пробелы
            date_str = date_str.strip()
            
            # Формат ISO с UTC
            if date_str.endswith('UTC'):
                return datetime.fromisoformat(date_str.replace('UTC', '+00:00'))
            
            # Формат ISO с таймзоной
            if '+' in date_str or 'Z' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Стандартный ISO формат
            return datetime.fromisoformat(date_str)
            
        except Exception as e:
            logger.warning(f"Не удалось парсить дату '{date_str}': {e}")
            return None
    
    def _parse_rbc_date_from_text(self, date_text: str) -> Optional[datetime]:
        """Парсинг даты из текста (например, '15 января 2024, 10:30')"""
        if not date_text:
            return None
        
        try:
            # Убираем лишние пробелы
            date_text = date_text.strip()
            
            # Словарь для русских месяцев
            months = {
                'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
                'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
                'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
            }
            
            # Паттерн для даты вида "15 января 2024, 10:30" или "15 января 2024"
            pattern = r'(\d{1,2})\s+(\w+)\s+(\d{4})(?:,\s*(\d{1,2}):(\d{2}))?'
            match = re.search(pattern, date_text)
            
            if match:
                day = int(match.group(1))
                month_name = match.group(2)
                year = int(match.group(3))
                hour = int(match.group(4)) if match.group(4) else 0
                minute = int(match.group(5)) if match.group(5) else 0
                
                if month_name in months:
                    month = months[month_name]
                    return datetime(year, month, day, hour, minute)
            
            # Паттерн для времени "сегодня", "вчера"
            if 'сегодня' in date_text.lower():
                time_match = re.search(r'(\d{1,2}):(\d{2})', date_text)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            if 'вчера' in date_text.lower():
                time_match = re.search(r'(\d{1,2}):(\d{2})', date_text)
                yesterday = datetime.now() - timedelta(days=1)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    return yesterday.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    return yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            
            return None
            
        except Exception as e:
            logger.warning(f"Не удалось парсить дату из текста '{date_text}': {e}")
            return None