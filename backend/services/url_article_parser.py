"""
Сервис для парсинга статей из любых URL с использованием Jina AI Reader API
"""

import aiohttp
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from pydantic import HttpUrl

logger = logging.getLogger(__name__)


class URLArticleParser:
    """
    Парсер статей из любых URL через Jina AI Reader API

    Jina AI Reader API - бесплатный сервис для конвертации веб-страниц в markdown
    Лимит: 1M запросов/месяц бесплатно
    Документация: https://jina.ai/reader
    """

    JINA_READER_BASE_URL = "https://r.jina.ai"
    REQUEST_TIMEOUT = 30  # секунд

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Инициализация HTTP сессии"""
        import ssl

        # Создаем SSL контекст с отключенной проверкой для development
        # В production это должно быть включено!
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()

    def _validate_url(self, url: str) -> bool:
        """
        Валидация URL

        Args:
            url: URL для проверки

        Returns:
            True если URL валиден, иначе False
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False

    def _extract_domain(self, url: str) -> str:
        """
        Извлечение домена из URL

        Args:
            url: URL

        Returns:
            Доменное имя
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return "unknown"

    def _clean_content(self, content: str) -> str:
        """
        Очистка контента от навигации, рекламы и лишних элементов

        Args:
            content: Исходный markdown контент

        Returns:
            Очищенный контент
        """
        import re

        # Удаляем ссылки на соцсети в формате [text](url)
        content = re.sub(r'\[.*?\]\(https?://(vk\.com|twitter\.com|facebook\.com|t\.me|instagram\.com|youtube\.com|ok\.ru|zen\.yandex\.ru)/[^\)]*\)', '', content)

        # Удаляем строки только с символами/эмодзи/иконками
        content = re.sub(r'^[\s\*\[\]()•▪▫◦‣⁃]+$', '', content, flags=re.MULTILINE)

        # Удаляем copyright и годы
        content = re.sub(r'©\s*\d{4}(-\d{4})?', '', content)

        # Удаляем email адреса
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', content)

        # Удаляем телефоны в формате +7, 8-800 и т.д.
        content = re.sub(r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}', '', content)

        # Удаляем ИНН, ОГРН, ОКПО (распространенные форматы)
        content = re.sub(r'\b(ИНН|ОГРН|ОКПО|КПП|ОКВЭД)[\s:]*\d+', '', content, flags=re.IGNORECASE)

        # Удаляем адреса (город, улица, дом)
        content = re.sub(r'\b(г\.|город|ул\.|улица|пр\.|проспект|д\.|дом)\s+[А-Яа-яёЁ0-9\s,.-]+', '', content)

        # Удаляем строки с количеством пользователей/просмотров
        content = re.sub(r'\*{2,}\s*(зарегистрированных|просмотров|пользователей)', '', content, flags=re.IGNORECASE)

        lines = content.split('\n')
        cleaned_lines = []
        skip_until_title = True

        for line in lines:
            # Пропускаем всё до первого заголовка Title: или первого H1
            if skip_until_title:
                if line.startswith('Title:') or line.startswith('# '):
                    skip_until_title = False
                    cleaned_lines.append(line)
                continue

            # Пропускаем строки с навигацией, рекламой, модальными окнами и footer
            if any(keyword in line.lower() for keyword in [
                # Авторизация и регистрация
                'image ', 'войти', 'вход', 'авторизуйтесь', 'авторизоваться', 'регистрация', 'зарегистрироваться',
                'комментарии', 'комментировать', 'загрузить еще',
                # Подписки и реклама
                'подписаться', 'подписка', 'реклама', 'banner', 'написать нам',
                # Cookie и модальные окна
                'cookie', 'принять', 'подтвердите', 'совершеннолетн', 'возраст', '18+',
                # Соцсети и мессенджеры
                '[](http', 'vk.com', 'telegram', 'поделиться', 'twitter', 'whatsapp', 'viber', 'skype',
                'facebook', 'youtube', 'instagram', 'яндекс.метрика',
                # Footer и контакты
                'рекламодателям', 'контакты', 'редакция', 'политика', 'оферта', 'пользовательское соглашение',
                'инн', 'огрн', 'окпо', 'юридический адрес', 'наименование организации', 'ооо', 'ао', 'зао',
                # Навигация
                'читайте также', 'о нас', 'мероприятия', 'эксперты', 'специальности', 'главная',
                # Дополнительный контент
                'воспроизведение материалов', 'источник:', 'фото:', 'видео:',
                'все права защищены', 'перепечатка', 'использование материалов',
                'новостная лента', 'популярное', 'популярные новости', 'рекомендуем', 'по теме',
                'смотрите также', 'больше новостей', 'следите за нами', 'ближайшие мероприятия',
                'условия использования', 'читать далее', 'подробнее'
            ]):
                continue

            # Пропускаем пустые строки подряд (больше 2)
            if not line.strip():
                if cleaned_lines and not cleaned_lines[-1].strip():
                    continue

            cleaned_lines.append(line)

        # Убираем лишние пустые строки в конце
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()

        return '\n'.join(cleaned_lines)

    def _extract_metadata(self, content: str) -> Dict[str, Optional[str]]:
        """
        Извлекает метаданные из markdown контента, полученного от Jina AI Reader

        Args:
            content: Markdown контент от Jina

        Returns:
            Словарь с метаданными: title, description, published_date, author
        """
        import re
        from datetime import datetime

        metadata = {
            'title': None,
            'description': None,
            'published_date': None,
            'author': None
        }

        lines = content.split('\n')

        for i, line in enumerate(lines):
            # Извлекаем Title (обычно в начале от Jina)
            if line.startswith('Title:') and not metadata['title']:
                metadata['title'] = line.replace('Title:', '').strip()

            # Извлекаем первый H1 как заголовок, если Title не найден
            elif line.startswith('# ') and not metadata['title']:
                metadata['title'] = line.replace('# ', '').strip()

            # Извлекаем URL Source (обычно следует за Title)
            elif line.startswith('URL Source:'):
                pass  # Уже есть в основном методе

            # Извлекаем Published Time
            elif line.startswith('Published Time:'):
                date_str = line.replace('Published Time:', '').strip()
                try:
                    # Попытка парсинга ISO формата
                    metadata['published_date'] = datetime.fromisoformat(date_str.replace('Z', '+00:00')).isoformat()
                except:
                    # Сохраняем как есть, если не удалось распарсить
                    metadata['published_date'] = date_str

            # Извлекаем Author (если есть)
            elif line.startswith('Author:'):
                metadata['author'] = line.replace('Author:', '').strip()

            # Ищем дату в тексте статьи (форматы: 06.10.2025, 2025-10-06)
            elif not metadata['published_date'] and i < 20:  # Ищем в первых 20 строках
                # Формат DD.MM.YYYY или DD-MM-YYYY
                date_match = re.search(r'\b(\d{2})[.\-/](\d{2})[.\-/](\d{4})\b', line)
                if date_match:
                    try:
                        day, month, year = date_match.groups()
                        metadata['published_date'] = f"{year}-{month}-{day}"
                    except:
                        pass

                # Формат YYYY-MM-DD
                date_match = re.search(r'\b(\d{4})[.\-/](\d{2})[.\-/](\d{2})\b', line)
                if date_match and not metadata['published_date']:
                    metadata['published_date'] = date_match.group(0)

        # Если description не найден, берем первый абзац после заголовка
        if not metadata['description']:
            found_title = False
            for line in lines:
                if line.startswith('Title:') or line.startswith('# '):
                    found_title = True
                    continue

                if found_title and line.strip() and not line.startswith('#') and not line.startswith('URL'):
                    # Берем первое предложение или первые 200 символов
                    desc = line.strip()
                    if len(desc) > 200:
                        desc = desc[:200] + '...'
                    metadata['description'] = desc
                    break

        return metadata

    async def _parse_via_trafilatura(self, url: str) -> Optional[str]:
        """
        Fallback парсинг через trafilatura для случаев, когда Jina не справился

        Args:
            url: URL для парсинга

        Returns:
            Извлеченный текст или None при ошибке
        """
        try:
            from trafilatura import fetch_url, extract

            logger.info(f"Attempting trafilatura fallback for URL: {url}")

            # Загружаем страницу
            downloaded = fetch_url(url)
            if not downloaded:
                logger.warning(f"Trafilatura: Failed to download URL: {url}")
                return None

            # Извлекаем контент с оптимальными настройками
            text = extract(
                downloaded,
                include_comments=False,  # Без комментариев
                include_tables=True,     # С таблицами (могут быть полезны в статьях)
                no_fallback=False,       # Использовать fallback методы
                favor_precision=True,    # Приоритет точности над полнотой
                deduplicate=True,        # Удалить дубликаты
            )

            if text and len(text) > 100:
                logger.info(f"Trafilatura extracted {len(text)} characters from {url}")
                return text
            else:
                logger.warning(f"Trafilatura: Content too short for URL: {url}")
                return None

        except ImportError:
            logger.warning("Trafilatura not installed. Install with: pip install trafilatura")
            return None
        except Exception as e:
            logger.error(f"Trafilatura error for {url}: {str(e)}", exc_info=True)
            return None

    async def parse_article(self, url: str) -> Dict[str, Any]:
        """
        Парсинг статьи из URL через Jina AI Reader

        Args:
            url: URL статьи для парсинга

        Returns:
            Словарь с данными статьи:
            {
                'success': bool,
                'url': str,
                'content': str,  # Текст статьи в markdown
                'domain': str,
                'title': Optional[str],  # Заголовок статьи
                'description': Optional[str],  # Краткое описание
                'published_date': Optional[str],  # Дата публикации
                'author': Optional[str],  # Автор
                'error': Optional[str]
            }
        """
        if not self._validate_url(url):
            return {
                'success': False,
                'url': url,
                'content': '',
                'domain': '',
                'error': 'Invalid URL format'
            }

        domain = self._extract_domain(url)

        # Параметры для Jina AI Reader:
        # - X-Return-Format: markdown (по умолчанию)
        # - X-With-Links-Summary: false (без списка ссылок в конце)
        # - X-With-Images-Summary: false (без списка изображений)
        # - X-No-Cache: false (использовать кеш)
        jina_url = f"{self.JINA_READER_BASE_URL}/{url}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'X-With-Links-Summary': 'false',
            'X-With-Images-Summary': 'false',
            # Целевые селекторы для извлечения основного контента
            'X-Target-Selector': 'article,main,.post-content,.article-body,.entry-content,.content,.post,.article-text',
            # Расширенный список элементов для удаления (модальные окна, footer, навигация, реклама)
            'X-Remove-Selector': 'nav,header,footer,aside,.sidebar,.advertisement,.social-share,#comments,.cookie-notice,.related-posts,.newsletter,.popup,.promo,.banner,.widget,.ad,#sidebar,.share-buttons,.author-box,.modal,.age-verification,.login-prompt,.auth-form,.registration-form,.gdpr-notice,.contact-info,.company-info,.legal-info,.breadcrumbs,.tags,.categories,.popular-posts,.recent-posts,.upcoming-events,.event-list,.social-links,.footer-menu,.header-menu,.site-nav,.site-footer,.site-header',
        }

        logger.info(f"Parsing article from URL: {url} via Jina AI Reader")

        try:
            if not self.session:
                raise RuntimeError("Session not initialized. Use 'async with' context manager.")

            async with self.session.get(jina_url) as response:
                if response.status == 200:
                    raw_content = await response.text()

                    # Очищаем контент от мусора
                    content = self._clean_content(raw_content)

                    # Проверяем что контент не пустой
                    if not content or len(content.strip()) < 100:
                        logger.warning(f"Content too short from Jina, trying trafilatura fallback for URL: {url}")

                        # Пробуем trafilatura как запасной вариант
                        fallback_content = await self._parse_via_trafilatura(url)

                        if fallback_content and len(fallback_content) > len(content):
                            logger.info(f"Trafilatura fallback successful for {url}")
                            # Пытаемся извлечь метаданные из оригинального контента
                            metadata = self._extract_metadata(raw_content)
                            return {
                                'success': True,
                                'url': url,
                                'content': fallback_content,
                                'domain': domain,
                                'title': metadata['title'],
                                'description': metadata['description'],
                                'published_date': metadata['published_date'],
                                'author': metadata['author'],
                                'error': None
                            }

                        return {
                            'success': False,
                            'url': url,
                            'content': content,
                            'domain': domain,
                            'title': None,
                            'description': None,
                            'published_date': None,
                            'author': None,
                            'error': 'Content too short or empty'
                        }

                    logger.info(f"Successfully parsed article from {url} (raw: {len(raw_content)} chars, cleaned: {len(content)} chars)")

                    # Извлекаем метаданные
                    metadata = self._extract_metadata(raw_content)

                    return {
                        'success': True,
                        'url': url,
                        'content': content,
                        'domain': domain,
                        'title': metadata['title'],
                        'description': metadata['description'],
                        'published_date': metadata['published_date'],
                        'author': metadata['author'],
                        'error': None
                    }
                else:
                    error_msg = f"HTTP {response.status}: {response.reason}"
                    logger.error(f"Failed to parse {url}: {error_msg}")
                    return {
                        'success': False,
                        'url': url,
                        'content': '',
                        'domain': domain,
                        'title': None,
                        'description': None,
                        'published_date': None,
                        'author': None,
                        'error': error_msg
                    }

        except aiohttp.ClientError as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(f"Jina failed for {url}, trying trafilatura: {error_msg}")

            # Пробуем trafilatura при сетевых ошибках Jina
            fallback_content = await self._parse_via_trafilatura(url)
            if fallback_content:
                return {
                    'success': True,
                    'url': url,
                    'content': fallback_content,
                    'domain': domain,
                    'title': None,
                    'description': None,
                    'published_date': None,
                    'author': None,
                    'error': None
                }

            return {
                'success': False,
                'url': url,
                'content': '',
                'domain': domain,
                'title': None,
                'description': None,
                'published_date': None,
                'author': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to parse {url}: {error_msg}", exc_info=True)
            return {
                'success': False,
                'url': url,
                'content': '',
                'domain': domain,
                'title': None,
                'description': None,
                'published_date': None,
                'author': None,
                'error': error_msg
            }

    async def parse_multiple_urls(self, urls: list[str]) -> list[Dict[str, Any]]:
        """
        Парсинг нескольких URL параллельно

        Args:
            urls: Список URL для парсинга

        Returns:
            Список результатов парсинга
        """
        import asyncio
        tasks = [self.parse_article(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Обрабатываем исключения
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'url': urls[i],
                    'content': '',
                    'domain': self._extract_domain(urls[i]),
                    'error': str(result)
                })
            else:
                processed_results.append(result)

        return processed_results


# Singleton instance для удобства использования
url_parser = URLArticleParser()
