"""
Сервис для публикации новостей в Bitrix CMS
"""

import httpx
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse, urlunparse
from core.config import settings

logger = logging.getLogger(__name__)


class BitrixService:
    """Сервис для взаимодействия с Bitrix CMS"""
    
    def __init__(self):
        # Старые настройки для обратной совместимости
        self.api_url = settings.BITRIX_API_URL
        self.api_token = settings.BITRIX_API_TOKEN
        self.iblock_id = settings.BITRIX_IBLOCK_ID
        
    def get_project_config(self, project_code: str) -> Dict[str, Any]:
        """
        Получает конфигурацию для указанного проекта из БД или из settings
        
        Args:
            project_code: Код проекта (GS, TS, PS)
            
        Returns:
            Dict с настройками проекта
        """
        try:
            # Пытаемся получить настройки из БД
            from services.settings_service import settings_service
            project_settings = settings_service.get_bitrix_project(project_code)
            
            if project_settings and project_settings.is_active:
                return {
                    "name": project_settings.project_name,
                    "display_name": project_settings.display_name,
                    "api_url": project_settings.api_url,
                    "api_token": project_settings.api_token,
                    "iblock_id": project_settings.iblock_id
                }
        except Exception as e:
            logger.warning(f"Failed to get project config from DB: {e}")
        
        # Fallback к настройкам из config.py
        if project_code not in settings.BITRIX_PROJECTS:
            raise ValueError(f"Неизвестный проект: {project_code}")
            
        return settings.BITRIX_PROJECTS[project_code]
    
    def get_available_projects(self) -> Dict[str, Dict[str, Any]]:
        """
        Получает список всех доступных проектов Bitrix из БД или из settings
        
        Returns:
            Dict со всеми настроенными проектами
        """
        try:
            # Пытаемся получить настройки из БД
            from services.settings_service import settings_service
            db_projects = settings_service.get_bitrix_projects()
            
            if db_projects:
                projects = {}
                for project in db_projects:
                    if project.is_active:
                        projects[project.project_code] = {
                            "name": project.project_name,
                            "display_name": project.display_name,
                            "api_url": project.api_url,
                            "api_token": project.api_token,
                            "iblock_id": project.iblock_id
                        }
                return projects
        except Exception as e:
            logger.warning(f"Failed to get available projects from DB: {e}")
        
        # Fallback к настройкам из config.py
        return settings.BITRIX_PROJECTS
    
    def prepare_html_for_bitrix(self, html_content: str) -> str:
        """
        Подготавливает HTML контент для Bitrix CMS
        Сохраняет HTML структуру и форматирование
        """
        if not html_content:
            return ""

        # Сохраняем исходный HTML, только выполняем минимальную очистку
        cleaned_html = html_content.strip()

        # Конвертируем теги в совместимые с Bitrix (если нужно)
        # Оставляем большинство HTML тегов как есть для полной поддержки форматирования

        # Битрикс поддерживает эти теги, но можем заменить на более совместимые:
        # cleaned_html = cleaned_html.replace('<strong>', '<b>').replace('</strong>', '</b>')
        # cleaned_html = cleaned_html.replace('<em>', '<i>').replace('</em>', '</i>')

        # НЕ убираем переносы строк - они важны для HTML структуры!
        # НЕ заменяем <br> теги - они нужны для правильного отображения

        # Убираем только лишние пробелы между тегами (но сохраняем переносы)
        import re
        cleaned_html = re.sub(r'>\s+<', '><', cleaned_html)

        return cleaned_html
        
    async def publish_article(
        self,
        title: str,
        preview_text: str,
        detail_text: str,
        project_code: Optional[str] = None,
        source: Optional[str] = None,
        main_type: Optional[int] = None,
        image_url: Optional[str] = None,
        seo_title: Optional[str] = None,
        seo_description: Optional[str] = None,
        seo_keywords: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Публикация статьи в Bitrix CMS
        
        Args:
            title: Заголовок статьи
            preview_text: Текст анонса
            detail_text: Полный текст статьи
            project_code: Код проекта (GS, TS, PS)
            source: Источник статьи
            main_type: ID главной нозологии
            image_url: URL изображения
            seo_title: SEO заголовок
            seo_description: SEO описание
            seo_keywords: SEO ключевые слова
            
        Returns:
            Dict с результатом публикации
        """
        try:
            # Определяем настройки проекта
            if project_code:
                logger.info(f"[Bitrix] publish_article: requested project_code={project_code}")
                project_config = self.get_project_config(project_code)
                api_url = project_config["api_url"]
                api_token = project_config["api_token"]
                iblock_id = project_config["iblock_id"]
                project_name = project_config["display_name"]
                logger.info(f"[Bitrix] Using project '{project_name}' (code={project_code}), api_url={api_url}, iblock_id={iblock_id}")
                
                # Проверяем настройки проекта
                if not api_url or not api_token:
                    return {
                        "success": False,
                        "error": f"Настройки для проекта {project_name} не настроены"
                    }
            else:
                # Используем настройки по умолчанию для обратной совместимости
                api_url = self.api_url
                api_token = self.api_token
                iblock_id = self.iblock_id
                project_name = "по умолчанию"
                logger.info(f"[Bitrix] No project_code provided, using defaults: api_url={api_url}, iblock_id={iblock_id}")
                
                if not api_url or not api_token:
                    return {
                        "success": False,
                        "error": "Настройки Bitrix API по умолчанию не настроены"
                    }
            
            # Подготавливаем HTML контент для Bitrix
            logger.info(f"[DEBUG] bitrix_service: incoming detail_text: {repr(detail_text[:300])}")
            prepared_detail_text = self.prepare_html_for_bitrix(detail_text)
            logger.info(f"[DEBUG] bitrix_service: prepared HTML content: {repr(prepared_detail_text[:300])}")
            
            # Формируем данные для отправки
            payload = {
                "title": title,
                "preview_text": preview_text,
                "detail_text": prepared_detail_text,
                "detail_text_type": "html"  # Явно указываем, что содержимое в HTML формате
            }
            
            # Добавляем опциональные поля
            if source:
                payload["source"] = source
                
            if main_type:
                payload["main_type"] = main_type
                
            if image_url:
                payload["image_url"] = image_url
                
            if seo_title:
                payload["seo_title"] = seo_title
                
            if seo_description:
                payload["seo_description"] = seo_description
                
            if seo_keywords:
                payload["seo_keywords"] = seo_keywords

            # Критичные поля маршрутизации на стороне Bitrix API
            # Передаем явно, чтобы API выбрало корректный сайт/инфоблок
            if iblock_id:
                payload["iblock_id"] = iblock_id
            if project_code:
                payload["project_code"] = project_code
            try:
                # name в конфиге — это домен проекта (gynecology.school / pediatrics.school / therapy.school)
                payload["site"] = project_config.get("name")
            except Exception:
                pass
            
            # Логируем финальный payload
            logger.info(f"[DEBUG] bitrix_service: final payload detail_text: {repr(payload.get('detail_text', '')[:300])}")
            
            # Отправляем запрос
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{api_url}?token={api_token}",
                    json=payload,
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                        "Accept": "application/json"
                    }
                )
                
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"Successfully published article to Bitrix {project_name}: ID {result.get('id')}")
                    returned_url = result.get("url")
                    fixed_url = returned_url
                    try:
                        desired_host = project_config.get("name") if project_code else None
                        if desired_host:
                            if returned_url and "://" in returned_url:
                                parts = urlparse(returned_url)
                                if parts.netloc and desired_host not in parts.netloc:
                                    parts = parts._replace(netloc=desired_host)
                                    fixed_url = urlunparse(parts)
                            elif returned_url:
                                # относительный путь
                                path = returned_url if returned_url.startswith('/') else f'/{returned_url}'
                                fixed_url = f"http://{desired_host}{path}"
                    except Exception as _:
                        fixed_url = returned_url
                    return {
                        "success": True,
                        "bitrix_id": result.get("id"),
                        "project": project_name,
                        "message": f"Статья успешно опубликована в {project_name}",
                        "url": fixed_url
                    }
                else:
                    logger.error(f"Bitrix API error: {result.get('error')}")
                    return {
                        "success": False,
                        "error": result.get("error", "Unknown Bitrix error")
                    }
            else:
                logger.error(f"HTTP error {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except httpx.TimeoutException:
            logger.error("Timeout when connecting to Bitrix API")
            return {
                "success": False,
                "error": "Timeout при подключении к Bitrix API"
            }
        except Exception as e:
            logger.error(f"Error publishing to Bitrix: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка публикации в Bitrix: {str(e)}"
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Тестирование подключения к Bitrix API
        
        Returns:
            Dict с результатом тестирования
        """
        if not self.api_token:
            return {
                "success": False,
                "error": "Bitrix API token не настроен"
            }
            
        if not self.api_url:
            return {
                "success": False,
                "error": "Bitrix API URL не настроен"
            }
            
        return {
            "success": True,
            "message": "Bitrix API настроен корректно",
            "config": {
                "url": self.api_url,
                "iblock_id": self.iblock_id,
                "token_configured": bool(self.api_token)
            }
        }


# Создаем глобальный экземпляр сервиса
bitrix_service = BitrixService()