"""
Планировщик для автоматической публикации новостей
"""

import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import BackgroundTasks

from services.news_generation_service import news_generation_service
from services.bitrix_service import bitrix_service
from database.models import NewsGenerationDraft, NewsStatus, moscow_now
from database.connection import DatabaseSession

logger = logging.getLogger(__name__)


class PublicationScheduler:
    """Планировщик автопубликации новостей"""
    
    def __init__(self):
        self.is_running = False
    
    async def process_scheduled_publications(self) -> int:
        """
        Обработка всех запланированных публикаций
        
        Returns:
            int: Количество опубликованных новостей
        """
        try:
            logger.info("Starting scheduled publications processing")
            
            # Получаем все готовые к публикации
            scheduled_draft_ids = news_generation_service.get_scheduled_publications()
            
            if not scheduled_draft_ids:
                logger.info("No scheduled publications found")
                return 0
            
            published_count = 0
            
            for draft_id in scheduled_draft_ids:
                try:
                    await self._publish_draft(draft_id)
                    published_count += 1
                    logger.info(f"Successfully published draft {draft_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to publish draft {draft_id}: {e}")
                    # Продолжаем обработку других черновиков
                    continue
            
            logger.info(f"Scheduled publications processing completed. Published: {published_count}")
            return published_count
            
        except Exception as e:
            logger.error(f"Error in process_scheduled_publications: {e}")
            return 0
    
    async def _publish_draft(self, draft_id: int):
        """
        Публикация конкретного черновика
        
        Args:
            draft_id: ID черновика для публикации
        """
        try:
            # Получаем черновик в новой сессии
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Draft {draft_id} not found")
                
                # Формируем контент из полей черновика
                generated_content = {
                    "news_text": draft.generated_news_text,
                    "seo_title": draft.generated_seo_title,
                    "seo_description": draft.generated_seo_description,
                    "seo_keywords": json.loads(draft.generated_seo_keywords) if draft.generated_seo_keywords else [],
                    "image_prompt": draft.generated_image_prompt,
                    "image_url": draft.generated_image_url
                }
                
                project_code = draft.published_project_code or "GS"
            
            # Публикуем в Bitrix
            result = await bitrix_service.publish_article(
                title=generated_content.get("seo_title", ""),
                preview_text=generated_content.get("seo_description", ""),
                detail_text=generated_content.get("news_text", ""),
                project_code=project_code,
                source=None,
                main_type=None,
                image_url=generated_content.get("image_url"),
                seo_title=generated_content.get("seo_title", ""),
                seo_description=generated_content.get("seo_description", ""),
                seo_keywords=", ".join(generated_content.get("seo_keywords", []))
            )
            
            if result["success"]:
                # Обновляем статус в БД
                self._mark_as_published(
                    draft_id=draft_id,
                    project_code=project_code,
                    project_name=result.get("project", "Неизвестный проект"),
                    bitrix_id=result.get("bitrix_id")
                )
                
                logger.info(f"Draft {draft_id} published successfully to Bitrix. ID: {result.get('bitrix_id')}")
                
                # Отправляем в Telegram
                await self._send_to_telegram(draft_id, result.get("url"))
                
            else:
                raise Exception(f"Bitrix publication failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error publishing draft {draft_id}: {e}")
            # Можно добавить логику для повторных попыток или уведомлений
            raise
    
    def _mark_as_published(
        self, 
        draft_id: int, 
        project_code: str, 
        project_name: str, 
        bitrix_id: Optional[int] = None
    ):
        """
        Отметить черновик как опубликованный
        
        Args:
            draft_id: ID черновика
            project_code: Код проекта
            project_name: Название проекта
            bitrix_id: ID в Bitrix
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if draft:
                    draft.status = "published"
                    draft.is_published = True
                    draft.published_at = moscow_now()
                    draft.published_project_code = project_code
                    draft.published_project_name = project_name
                    draft.bitrix_id = bitrix_id
                    
                    session.commit()
                    logger.info(f"Marked draft {draft_id} as published")
                
        except Exception as e:
            logger.error(f"Error marking draft {draft_id} as published: {e}")
            raise
    
    async def start_scheduler(self, interval_minutes: int = 1):
        """
        Запуск планировщика
        
        Args:
            interval_minutes: Интервал проверки в минутах
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        logger.info(f"Starting publication scheduler with {interval_minutes} minute interval")
        
        try:
            while self.is_running:
                await self.process_scheduled_publications()
                
                # Ждем указанный интервал
                await asyncio.sleep(interval_minutes * 60)
                
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        finally:
            self.is_running = False
            logger.info("Publication scheduler stopped")
    
    def stop_scheduler(self):
        """Остановка планировщика"""
        self.is_running = False
        logger.info("Stopping publication scheduler")
    
    async def _send_to_telegram(self, draft_id: int, article_url: Optional[str] = None):
        """
        Отправка статьи в Telegram
        
        Args:
            draft_id: ID черновика
            article_url: URL опубликованной статьи
        """
        try:
            # Импортируем функцию отправки в Telegram
            from api.news_generation import send_to_telegram
            
            # Получаем черновик для данных
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    logger.error(f"Draft {draft_id} not found for Telegram sending")
                    return
                
                # Используем сохранённый TG-пост и добавляем ссылку аналогично публикации сразу
                base_tg_post = draft.generated_tg_post
                if not base_tg_post:
                    # Фолбэк: создаём простой пост из заголовка
                    title = draft.generated_seo_title or "Новая статья"
                    base_tg_post = f"<b>{title}</b>"
                
                # Добавляем ссылку к готовому посту (как при публикации сразу)
                if article_url:
                    separator = "\n" if not base_tg_post.endswith("\n") else ""
                    tg_text = f"{base_tg_post}{separator}— {article_url}"
                else:
                    tg_text = base_tg_post
                
                # Отправляем в Telegram с изображением если есть
                await send_to_telegram(
                    text=tg_text,
                    photo_url=draft.generated_image_url
                )
                
                logger.info(f"Successfully sent draft {draft_id} to Telegram")
                
        except Exception as e:
            logger.error(f"Failed to send draft {draft_id} to Telegram: {e}")


# Глобальный экземпляр планировщика
publication_scheduler = PublicationScheduler()


# Функция для запуска планировщика в background
async def start_publication_scheduler():
    """Запуск планировщика в фоновом режиме"""
    await publication_scheduler.start_scheduler(interval_minutes=1)


# Функция для ручного запуска обработки (для тестирования)
async def process_scheduled_publications_now() -> int:
    """Ручная обработка запланированных публикаций"""
    return await publication_scheduler.process_scheduled_publications()