"""
Парсер для Remedium.ru
"""

import aiohttp
import ssl
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin
import re
from datetime import datetime
import logging

from models.schemas import NewsSource
from services.base_parser import BaseNewsParser

logger = logging.getLogger(__name__)

class RemediumParser(BaseNewsParser):
    """Парсер для сайта Remedium.ru"""
    
    def __init__(self):
        super().__init__(source_name="remedium", base_url="https://remedium.ru")
        self.news_url = f"{self.base_url}/news/"
    
    async def parse_news_list(self, max_articles: int = 10, date_filter: Optional[str] = None, fetch_full_content: bool = True) -> List[NewsSource]:
        """Парсинг списка новостей с главной страницы"""
        articles = await self.parse_news(limit=max_articles)
        
        # Если нужен полный контент, загружаем его для каждой статьи
        if fetch_full_content and articles:
            logger.info(f"Загружаем полный контент для {len(articles)} статей Remedium")
            for i, article in enumerate(articles):
                try:
                    full_article = await self.fetch_full_article(article.url)
                    if full_article and full_article.content:
                        articles[i].content = full_article.content
                        logger.info(f"Загружен полный контент для статьи: {article.title[:50]}...")
                except Exception as e:
                    logger.warning(f"Не удалось загрузить полный контент для {article.url}: {e}")
        
        return articles
    
    async def _fetch_full_article(self, url: str) -> Optional[NewsSource]:
        """Получение полного текста статьи"""
        return await self.fetch_full_article(url)
    
    def _extract_article_metadata(self, soup: BeautifulSoup) -> dict:
        """Извлечение метаданных статьи"""
        metadata = {
            'published_date': None,
            'author': '',
            'views': 0
        }
        
        # Дата публикации
        time_elem = soup.find('time', {'datetime': True})
        if time_elem:
            datetime_str = time_elem.get('datetime')
            try:
                if ' ' in datetime_str:
                    date_part = datetime_str.split(' ')[0]
                    day, month, year = date_part.split('.')
                    metadata['published_date'] = datetime(int(year), int(month), int(day))
                else:
                    metadata['published_date'] = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        # Автор
        author_selectors = [
            '.b-article__author',
            '.article-author',
            '.post-author',
            '.author'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                metadata['author'] = author_elem.get_text(strip=True)
                break
        
        # Проверяем мета-теги для автора
        if not metadata['author']:
            author_meta = soup.find('meta', {'name': 'author'})
            if author_meta:
                metadata['author'] = author_meta.get('content', '')
        
        return metadata
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """Получение HTML страницы"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Ошибка загрузки страницы {url}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка получения страницы {url}: {e}")
            return None

    async def parse_news(self, limit: int = 20) -> List[NewsSource]:
        """Парсинг новостей с поддержкой пагинации"""
        
        try:
            articles = []
            seen_urls = set()  # Для отслеживания уникальных URL
            page = 1528  # Начинаем с первой страницы (самые новые)
            articles_per_page = 39  # На каждой странице ~39 элементов
            
            while len(articles) < limit:
                # Формируем URL для текущей страницы
                page_url = f"{self.news_url}?PAGEN_2={page}"
                logger.info(f"Парсинг страницы {1528 - page + 1}: {page_url}")
                
                html = await self.fetch_page(page_url)
                if not html:
                    logger.warning(f"Не удалось загрузить страницу {page}")
                    break
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Ищем новостные элементы
                news_items = soup.find_all('div', class_='b-section-item')
                
                if not news_items:
                    logger.info("Новостные элементы не найдены, завершаем парсинг")
                    break
                
                page_articles = []
                for item in news_items:
                    # Проверяем, что это не видеозаметка
                    if self._is_video_note(item):
                        continue
                        
                    article_data = self._extract_article_data(item)
                    if article_data and article_data.url not in seen_urls:
                        seen_urls.add(article_data.url)
                        page_articles.append(article_data)
                        
                        # Если достигли лимита, прерываем
                        if len(articles) + len(page_articles) >= limit:
                            break
                
                articles.extend(page_articles)
                
                logger.info(f"Со страницы {1528 - page + 1} получено {len(page_articles)} уникальных статей")
                
                # Если на странице мало статей и мы еще не достигли лимита, продолжаем
                if len(page_articles) < 5 and len(articles) < limit * 0.8:
                    logger.info("Мало статей на странице, но продолжаем поиск")
                elif len(page_articles) == 0:
                    logger.info("Статьи не найдены, завершаем парсинг")
                    break
                
                # Переходим к следующей странице (более старые новости)
                page -= 1
                
                # Защита от бесконечного цикла - увеличиваем диапазон поиска
                if page < 1400:  # Расширяем диапазон поиска
                    logger.warning("Достигнута минимальная страница поиска")
                    break
            
            # Обрезаем до нужного лимита
            articles = articles[:limit]
            
            logger.info(f"Найдено {len(articles)} уникальных статей с Remedium.ru")
            return articles
            
        except Exception as e:
            logger.error(f"Ошибка парсинга Remedium.ru: {e}")
            return []
    
    def _is_video_note(self, item) -> bool:
        """Проверяет, является ли элемент видеозаметкой врача"""
        try:
            # Проверяем, находится ли элемент внутри карусели (owl-carousel)
            parent = item.parent
            while parent:
                if parent.name and parent.get('class'):
                    parent_classes = ' '.join(parent.get('class', []))
                    # Если элемент находится внутри карусели или секции с видеозаметками
                    if ('owl-carousel' in parent_classes or 
                        'l-sect-ind-cust' in parent_classes or
                        'owl-stage' in parent_classes or
                        'owl-item' in parent_classes):
                        return True
                parent = parent.parent
            
            # Ищем текст "Видеозаметки врача" в элементе
            item_text = item.get_text()
            if 'Видеозаметки врача' in item_text or 'видеозаметк' in item_text.lower():
                return True
            
            # Проверяем заголовок
            title_elem = item.find('div', class_='b-section-item__title')
            if title_elem:
                title_text = title_elem.get_text(strip=True).lower()
                if 'видеозаметк' in title_text or 'видео' in title_text:
                    return True
            
            # Проверяем ссылку
            title_link = item.find('a')
            if title_link:
                href = title_link.get('href', '')
                if 'video' in href or 'видео' in href:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка проверки видеозаметки: {e}")
            return False
    
    def _extract_article_data(self, item) -> Optional[NewsSource]:
        """Извлечение данных статьи из элемента"""
        
        try:
            # Заголовок и ссылка
            title_elem = item.find('div', class_='b-section-item__title')
            if not title_elem:
                return None
            
            title_link = title_elem.find('a')
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            href = title_link.get('href')
            if not href:
                return None
            
            url = urljoin(self.base_url, href)
            
            # Описание
            description = ""
            desc_elem = item.find('div', class_='b-section-item__desc')
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Дата публикации
            published_date = None
            
            # Сначала ищем в элементе time (более надежный способ)
            time_elem = item.find('time', {'datetime': True})
            if time_elem:
                datetime_str = time_elem.get('datetime')
                try:
                    # Парсим дату в формате "31.07.2025 12:40:01"
                    if ' ' in datetime_str:
                        date_part = datetime_str.split(' ')[0]
                        day, month, year = date_part.split('.')
                        published_date = datetime(int(year), int(month), int(day))
                    else:
                        # Пытаемся парсить ISO формат
                        published_date = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            
            # Если не нашли в time, ищем в meta элементах текущего item
            if not published_date:
                meta_elem = item.find('div', class_='b-section-item__meta')
                if meta_elem:
                    meta_text = meta_elem.get_text(strip=True)
                    # Пытаемся распарсить дату в формате DD.MM.YYYY
                    date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', meta_text)
                    if date_match:
                        day, month, year = date_match.groups()
                        try:
                            published_date = datetime(int(year), int(month), int(day))
                        except ValueError:
                            pass
            
            # Если все еще не нашли дату, ищем в соседних элементах
            if not published_date:
                # Ищем в родительском элементе
                parent = item.parent
                if parent:
                    # Ищем все meta элементы в родителе
                    all_meta_elems = parent.find_all(class_='b-section-item__meta')
                    for meta_elem in all_meta_elems:
                        meta_text = meta_elem.get_text(strip=True)
                        date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', meta_text)
                        if date_match:
                            day, month, year = date_match.groups()
                            try:
                                published_date = datetime(int(year), int(month), int(day))
                                break
                            except ValueError:
                                continue
            
            # Последняя попытка - ищем в любых meta элементах на странице
            if not published_date:
                # Получаем корневой элемент страницы
                root = item
                while root.parent:
                    root = root.parent
                
                # Ищем все элементы с датами
                date_elements = root.find_all(class_='b-section-item__meta')
                if date_elements:
                    # Берем первую найденную дату
                    for date_elem in date_elements:
                        date_text = date_elem.get_text(strip=True)
                        date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', date_text)
                        if date_match:
                            day, month, year = date_match.groups()
                            try:
                                published_date = datetime(int(year), int(month), int(day))
                                logger.info(f"Найдена дата в глобальном поиске: {published_date}")
                                break
                            except ValueError:
                                continue
            
            # Изображение
            image_url = None
            picture_elem = item.find('div', class_='b-section-item__picture')
            if picture_elem:
                img = picture_elem.find('img')
                if img:
                    img_src = img.get('src') or img.get('data-src')
                    if img_src and not img_src.startswith('data:'):
                        image_url = urljoin(self.base_url, img_src)
            
            return NewsSource(
                title=title,
                url=url,
                content=description,  # Используем description как content
                published_date=published_date,
                source_site=self.source_name
            )
            
        except Exception as e:
            logger.error(f"Ошибка извлечения данных статьи: {e}")
            return None
    
    async def fetch_full_article(self, url: str) -> Optional[NewsSource]:
        """Получение полного текста статьи"""
        
        try:
            html = await self.fetch_page(url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            return self._extract_full_article_content(soup, url)
            
        except Exception as e:
            logger.error(f"Ошибка получения полного текста статьи {url}: {e}")
            return None
    
    def _extract_full_article_content(self, soup: BeautifulSoup, url: str) -> Optional[NewsSource]:
        """Извлечение полного содержимого статьи"""
        
        try:
            # Заголовок
            title = ""
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Контент статьи
            content = ""
            content_selectors = [
                '.b-news-detail-body',  # Основной селектор для Remedium
                '.b-article__content',
                '.article-content',
                '.post-content',
                '.content',
                'article .text'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Удаляем ненужные элементы
                    for unwanted in content_elem.find_all(['script', 'style', 'nav', 'aside', 'meta', 'link']):
                        unwanted.decompose()
                    
                    # Для Remedium извлекаем весь текст, включая <br> теги
                    if selector == '.b-news-detail-body':
                        # Заменяем <br> на переносы строк
                        for br in content_elem.find_all('br'):
                            br.replace_with('\n')
                        
                        # Получаем весь текст
                        content = content_elem.get_text(separator='\n', strip=True)
                        
                        # Удаляем "Список литературы / References" и все что после него
                        references_patterns = [
                            r'Список литературы\s*/\s*References.*',
                            r'Список литературы.*',
                            r'References\s*Развернуть.*',
                            r'References.*',
                            r'ЛИТЕРАТУРА.*',
                            r'БИБЛИОГРАФИЯ.*',
                            r'\[1\].*',  # Удаляем все что начинается с [1] (нумерованные ссылки)
                            r'^\d+\.\s+[А-ЯA-Z].*doi:.*',  # Удаляем пронумерованные ссылки с doi
                        ]
                        
                        for pattern in references_patterns:
                            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
                        
                        # Очищаем от лишних переносов
                        content = re.sub(r'\n\s*\n', '\n\n', content)
                        content = content.strip()
                    else:
                        # Для других селекторов используем старую логику
                        paragraphs = content_elem.find_all(['p', 'div'])
                        content_parts = []
                        
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            if text and len(text) > 20:  # Фильтруем короткие фрагменты
                                content_parts.append(text)
                        
                        content = '\n\n'.join(content_parts)
                    
                    if content:  # Если нашли контент, выходим из цикла
                        break
            
            # Если контент не найден, пытаемся извлечь из всех параграфов
            if not content:
                paragraphs = soup.find_all('p')
                content_parts = []
                
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        content_parts.append(text)
                
                content = '\n\n'.join(content_parts)
            
            # Дата публикации
            published_date = None
            
            # Ищем в элементе time
            time_elem = soup.find('time', {'datetime': True})
            if time_elem:
                datetime_str = time_elem.get('datetime')
                try:
                    # Парсим дату в формате "30.07.2025 22:30:00"
                    if ' ' in datetime_str:
                        date_part = datetime_str.split(' ')[0]
                        day, month, year = date_part.split('.')
                        published_date = datetime(int(year), int(month), int(day))
                    else:
                        # Пытаемся парсить ISO формат
                        published_date = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            
            # Автор
            author = ""
            author_selectors = [
                '.b-article__author',
                '.article-author',
                '.post-author',
                '.author'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break
            
            # Проверяем мета-теги для автора
            if not author:
                author_meta = soup.find('meta', {'name': 'author'})
                if author_meta:
                    author = author_meta.get('content', '')
            
            return NewsSource(
                title=title,
                content=content,
                published_date=published_date,
                author=author,
                url=url,
                source_site=self.source_name
            )
            
        except Exception as e:
            logger.error(f"Ошибка извлечения содержимого статьи: {e}")
            return None