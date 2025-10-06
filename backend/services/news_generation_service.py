"""
Сервис для работы с базой данных для генерации новостей
"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from database.connection import DatabaseSession
from database.models import moscow_now
from database.models import (
    Article, NewsGenerationDraft, GenerationLog, ProjectType, PublicationLog
)
from database.schemas import NewsGenerationDraftRead, GenerationLogRead

logger = logging.getLogger(__name__)


class NewsGenerationService:
    """Сервис для работы с генерацией новостей"""
    
    @staticmethod
    def create_draft(
        article_id: int,
        project: ProjectType,
        summary: str,
        facts: List[str],
        created_by: Optional[int] = None,
    ) -> int:
        """
        Создание черновика генерации новости
        
        Args:
            article_id: ID оригинальной статьи
            project: Тип проекта
            summary: Выжимка статьи
            facts: Список фактов
            created_by: ID пользователя, создавшего черновик
            
        Returns:
            int: ID созданного черновика
        """
        try:
            with DatabaseSession() as session:
                # Проверяем существование статьи
                article = session.get(Article, article_id)
                if not article:
                    raise ValueError(f"Статья с ID {article_id} не найдена")
                
                # Приводим тип проекта к enum БД на случай если пришла строка/другой enum
                try:
                    if not isinstance(project, ProjectType):
                        project = ProjectType(str(project))
                except Exception:
                    project = ProjectType.THERAPY

                # Создаем новый черновик
                draft = NewsGenerationDraft(
                    article_id=article_id,
                    project=project,
                    summary=summary,
                    facts=json.dumps(facts, ensure_ascii=False),
                    status="summary_pending",
                    created_by=created_by,
                )
                
                session.add(draft)
                session.commit()
                session.refresh(draft)
                
                logger.info(f"Created draft {draft.id} for article {article_id}")
                return draft.id
                
        except Exception as e:
            logger.error(f"Error creating draft: {e}")
            raise
    
    @staticmethod
    def update_draft_status(draft_id: int, status: str, summary: Optional[str] = None, facts: Optional[List[str]] = None) -> bool:
        """
        Обновление статуса черновика
        
        Args:
            draft_id: ID черновика
            status: Новый статус
            summary: Обновленная выжимка (опционально)
            facts: Обновленные факты (опционально)
            
        Returns:
            bool: Успешность операции
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")
                
                draft.status = status
                draft.updated_at = moscow_now()
                
                if summary is not None:
                    draft.summary = summary
                
                if facts is not None:
                    draft.facts = json.dumps(facts, ensure_ascii=False)
                
                session.commit()
                logger.info(f"Updated draft {draft_id} status to {status}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating draft status: {e}")
            raise
    
    @staticmethod
    def update_publication_info(draft_id: int, project_code: str, project_name: str, bitrix_id: int, published_by: Optional[int] = None) -> bool:
        """
        Создание записи о публикации (с поддержкой новой таблицы publications и обратной совместимости)

        Args:
            draft_id: ID черновика
            project_code: Код проекта (GS, TS, PS)
            project_name: Название проекта
            bitrix_id: ID в Bitrix CMS
            published_by: ID пользователя, опубликовавшего статью

        Returns:
            bool: Успешность операции
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")


                # Обновляем черновик
                draft.status = "published"
                draft.is_published = True
                draft.published_project_code = project_code
                draft.published_project_name = project_name
                draft.bitrix_id = bitrix_id
                draft.published_at = moscow_now()
                draft.updated_at = moscow_now()

                session.commit()
                logger.info(f"Updated draft {draft_id} publication info: project={project_code}, bitrix_id={bitrix_id}")
                return True

        except Exception as e:
            logger.error(f"Error updating publication info: {e}")
            raise
    
    @staticmethod
    def save_generated_content(draft_id: int, generated_content: Dict[str, Any]) -> bool:
        """
        Сохранение сгенерированного контента в черновик
        
        Args:
            draft_id: ID черновика
            generated_content: Сгенерированный контент
            
        Returns:
            bool: Успешность операции
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")
                
                # Сохраняем сгенерированный контент как есть
                # Вся обработка теперь происходит в prepare_html_for_bitrix
                news_text = generated_content.get("news_text", "")
                logger.info(f"[DEBUG] save_generated_content: incoming news_text: {repr(news_text[:300])}")
                draft.generated_news_text = news_text
                logger.info(f"[DEBUG] Final saved news_text: {repr(draft.generated_news_text[:300])}")
                draft.generated_seo_title = generated_content.get("seo_title")
                draft.generated_seo_description = generated_content.get("seo_description")
                draft.generated_seo_keywords = json.dumps(generated_content.get("seo_keywords", []), ensure_ascii=False)
                draft.generated_image_prompt = generated_content.get("image_prompt")
                draft.generated_image_url = generated_content.get("image_url")

                # Сохраняем важные статусы при редактировании
                if draft.status not in ["scheduled", "published"]:
                    draft.status = "generated"

                draft.updated_at = moscow_now()
                
                session.commit()
                logger.info(f"Saved generated content for draft {draft_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving generated content: {e}")
            raise

    @staticmethod
    def save_telegram_post(draft_id: int, tg_post: str) -> bool:
        """
        Сохранение анонса для Telegram в поле generated_seo_description (временное хранение)
        или при наличии отдельного поля — туда. Здесь сохраняем в отдельное поле черновика.
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")

                # Храним ТГ-пост в отдельном поле, если оно есть; иначе — в служебном
                if hasattr(draft, "generated_tg_post"):
                    draft.generated_tg_post = tg_post
                else:
                    draft.generated_image_prompt = tg_post
                draft.updated_at = moscow_now()

                session.commit()
                logger.info(f"Saved Telegram post for draft {draft_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving telegram post: {e}")
            raise
    
    @staticmethod
    def update_scheduled_time(draft_id: int, scheduled_at: Optional[datetime] = None) -> bool:
        """
        Обновление времени запланированной публикации

        Args:
            draft_id: ID черновика
            scheduled_at: Новое время публикации (None для отмены планирования)

        Returns:
            bool: Успешность операции
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")

                draft.scheduled_at = scheduled_at
                draft.updated_at = moscow_now()

                session.commit()
                logger.info(f"Updated scheduled time for draft {draft_id} to {scheduled_at}")
                return True

        except Exception as e:
            logger.error(f"Error updating scheduled time: {e}")
            raise

    @staticmethod
    def update_image_url(draft_id: int, new_image_url: str, new_prompt: Optional[str] = None) -> bool:
        """
        Обновление URL изображения в черновике
        
        Args:
            draft_id: ID черновика
            new_image_url: Новый URL изображения
            new_prompt: Новый промпт (опционально)
            
        Returns:
            bool: Успешность операции
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")
                
                draft.generated_image_url = new_image_url
                # Не перезаписываем generated_image_prompt/generated_tg_post — там хранится tg_post
                draft.updated_at = moscow_now()
                
                session.commit()
                logger.info(f"Updated image URL for draft {draft_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating image URL: {e}")
            raise
    
    @staticmethod
    def get_draft(draft_id: int) -> Optional[NewsGenerationDraftRead]:
        """
        Получение черновика по ID
        
        Args:
            draft_id: ID черновика
            
        Returns:
            Optional[NewsGenerationDraftRead]: Черновик или None
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    return None
                
                return NewsGenerationDraftRead(
                    id=draft.id,
                    article_id=draft.article_id,
                    project=draft.project,
                    summary=draft.summary,
                    facts=draft.facts,
                    generated_news_text=draft.generated_news_text,
                    generated_seo_title=draft.generated_seo_title,
                    generated_seo_description=draft.generated_seo_description,
                    generated_seo_keywords=draft.generated_seo_keywords,
                    generated_image_prompt=draft.generated_image_prompt,
                    generated_image_url=draft.generated_image_url,
                    status=draft.status,
                    # Поля для отслеживания ошибок
                    last_error_message=draft.last_error_message,
                    last_error_step=draft.last_error_step,
                    last_error_at=draft.last_error_at,
                    can_retry=draft.can_retry or True,
                    retry_count=draft.retry_count or 0,
                    # Информация о публикации
                    is_published=draft.is_published or False,
                    published_project_code=draft.published_project_code,
                    published_project_name=draft.published_project_name,
                    bitrix_id=draft.bitrix_id,
                    published_at=draft.published_at,
                    scheduled_at=draft.scheduled_at,
                    created_at=draft.created_at,
                    updated_at=draft.updated_at
                )

        except Exception as e:
            logger.error(f"Error getting draft: {e}")
            raise

    @staticmethod
    def get_draft_by_article_and_project(article_id: int, project: str) -> Optional[NewsGenerationDraftRead]:
        """
        Получение черновика по ID статьи и проекту

        Args:
            article_id: ID статьи
            project: Тип проекта

        Returns:
            Optional[NewsGenerationDraftRead]: Черновик или None
        """
        try:
            with DatabaseSession() as session:
                # Ищем черновик для данной статьи и проекта, отсортированный по дате создания (самый новый)
                from sqlmodel import select
                draft = session.exec(
                    select(NewsGenerationDraft)
                    .where(NewsGenerationDraft.article_id == article_id)
                    .where(NewsGenerationDraft.project == project)
                    .order_by(NewsGenerationDraft.created_at.desc())
                ).first()

                if not draft:
                    return None

                return NewsGenerationDraftRead(
                    id=draft.id,
                    article_id=draft.article_id,
                    project=draft.project,
                    summary=draft.summary,
                    facts=draft.facts,
                    generated_news_text=draft.generated_news_text,
                    generated_seo_title=draft.generated_seo_title,
                    generated_seo_description=draft.generated_seo_description,
                    generated_seo_keywords=draft.generated_seo_keywords,
                    generated_image_prompt=draft.generated_image_prompt,
                    generated_image_url=draft.generated_image_url,
                    status=draft.status,
                    # Поля для отслеживания ошибок
                    last_error_message=draft.last_error_message,
                    last_error_step=draft.last_error_step,
                    last_error_at=draft.last_error_at,
                    can_retry=draft.can_retry or True,
                    retry_count=draft.retry_count or 0,
                    # Информация о публикации
                    is_published=draft.is_published or False,
                    published_project_code=draft.published_project_code,
                    published_project_name=draft.published_project_name,
                    bitrix_id=draft.bitrix_id,
                    published_at=draft.published_at,
                    scheduled_at=draft.scheduled_at,
                    created_at=draft.created_at,
                    updated_at=draft.updated_at
                )

        except Exception as e:
            logger.error(f"Error getting draft by article and project: {e}")
            raise

    @staticmethod
    def get_drafts_by_article(article_id: int) -> List[NewsGenerationDraftRead]:
        """
        Получение всех черновиков для статьи
        
        Args:
            article_id: ID статьи
            
        Returns:
            List[NewsGenerationDraftRead]: Список черновиков
        """
        try:
            with DatabaseSession() as session:
                drafts = session.exec(
                    select(NewsGenerationDraft)
                    .where(NewsGenerationDraft.article_id == article_id)
                    .order_by(NewsGenerationDraft.created_at.desc())
                ).all()

                return [
                    NewsGenerationDraftRead(
                        id=draft.id,
                        article_id=draft.article_id,
                        project=draft.project,
                        summary=draft.summary,
                        facts=draft.facts,
                        generated_news_text=draft.generated_news_text,
                        generated_seo_title=draft.generated_seo_title,
                        generated_seo_description=draft.generated_seo_description,
                        generated_seo_keywords=draft.generated_seo_keywords,
                        generated_image_prompt=draft.generated_image_prompt,
                        generated_image_url=draft.generated_image_url,
                        status=draft.status,
                        # Поля для отслеживания ошибок
                        last_error_message=draft.last_error_message,
                        last_error_step=draft.last_error_step,
                        last_error_at=draft.last_error_at,
                        can_retry=draft.can_retry or True,
                        retry_count=draft.retry_count or 0,
                        # Информация о публикации
                        is_published=draft.is_published or False,
                        published_project_code=draft.published_project_code,
                        published_project_name=draft.published_project_name,
                        bitrix_id=draft.bitrix_id,
                        published_at=draft.published_at,
                        created_at=draft.created_at,
                        updated_at=draft.updated_at
                    )
                    for draft in drafts
                ]
                
        except Exception as e:
            logger.error(f"Error getting drafts by article: {e}")
            raise
    
    @staticmethod
    def get_all_drafts(limit: int = 50, offset: int = 0, status: Optional[str] = None) -> List[NewsGenerationDraftRead]:
        """
        Получение всех черновиков с пагинацией
        
        Args:
            limit: Лимит записей
            offset: Смещение
            status: Фильтр по статусу
            
        Returns:
            List[NewsGenerationDraftRead]: Список черновиков
        """
        try:
            with DatabaseSession() as session:
                query = select(NewsGenerationDraft)
                
                if status:
                    query = query.where(NewsGenerationDraft.status == status)
                
                query = query.order_by(NewsGenerationDraft.created_at.desc()).offset(offset).limit(limit)
                
                drafts = session.exec(query).all()

                return [
                    NewsGenerationDraftRead(
                        id=draft.id,
                        article_id=draft.article_id,
                        project=draft.project,
                        summary=draft.summary,
                        facts=draft.facts,
                        generated_news_text=draft.generated_news_text,
                        generated_seo_title=draft.generated_seo_title,
                        generated_seo_description=draft.generated_seo_description,
                        generated_seo_keywords=draft.generated_seo_keywords,
                        generated_image_prompt=draft.generated_image_prompt,
                        generated_image_url=draft.generated_image_url,
                        status=draft.status,
                        # Поля для отслеживания ошибок
                        last_error_message=draft.last_error_message,
                        last_error_step=draft.last_error_step,
                        last_error_at=draft.last_error_at,
                        can_retry=draft.can_retry or True,
                        retry_count=draft.retry_count or 0,
                        # Информация о публикации
                        is_published=draft.is_published or False,
                        published_project_code=draft.published_project_code,
                        published_project_name=draft.published_project_name,
                        bitrix_id=draft.bitrix_id,
                        published_at=draft.published_at,
                        created_at=draft.created_at,
                        updated_at=draft.updated_at
                    )
                    for draft in drafts
                ]
                
        except Exception as e:
            logger.error(f"Error getting all drafts: {e}")
            raise
    
    @staticmethod
    def log_generation_operation(
        draft_id: int,
        operation_type: str,
        model_used: str,
        success: bool,
        tokens_used: Optional[int] = None,
        processing_time_seconds: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> int:
        """
        Логирование операции генерации
        
        Args:
            draft_id: ID черновика
            operation_type: Тип операции (summary, generation, image_regeneration)
            model_used: Использованная модель
            success: Успешность операции
            tokens_used: Количество использованных токенов
            processing_time_seconds: Время обработки в секундах
            error_message: Сообщение об ошибке
            
        Returns:
            int: ID созданной записи лога
        """
        try:
            with DatabaseSession() as session:
                log_entry = GenerationLog(
                    draft_id=draft_id,
                    operation_type=operation_type,
                    model_used=model_used,
                    success=success,
                    tokens_used=tokens_used,
                    processing_time_seconds=processing_time_seconds,
                    error_message=error_message
                )
                
                session.add(log_entry)
                session.commit()
                session.refresh(log_entry)
                
                logger.info(f"Logged generation operation {log_entry.id}")
                return log_entry.id
                
        except Exception as e:
            logger.error(f"Error logging generation operation: {e}")
            raise
    
    @staticmethod
    def get_generation_logs(draft_id: Optional[int] = None, limit: int = 50) -> List[GenerationLogRead]:
        """
        Получение логов генерации
        
        Args:
            draft_id: ID черновика для фильтрации (опционально)
            limit: Лимит записей
            
        Returns:
            List[GenerationLogRead]: Список логов
        """
        try:
            with DatabaseSession() as session:
                query = select(GenerationLog)
                
                if draft_id:
                    query = query.where(GenerationLog.draft_id == draft_id)
                
                query = query.order_by(GenerationLog.created_at.desc()).limit(limit)
                
                logs = session.exec(query).all()
                
                return [
                    GenerationLogRead(
                        id=log.id,
                        draft_id=log.draft_id,
                        operation_type=log.operation_type,
                        model_used=log.model_used,
                        success=log.success,
                        error_message=log.error_message,
                        tokens_used=log.tokens_used,
                        processing_time_seconds=log.processing_time_seconds,
                        created_at=log.created_at
                    )
                    for log in logs
                ]
                
        except Exception as e:
            logger.error(f"Error getting generation logs: {e}")
            raise


    @staticmethod
    def get_publications(limit: int = 100) -> List[Dict[str, Any]]:
        """Получить список публикаций (из черновиков со статусом is_published=True)."""
        try:
            with DatabaseSession() as session:
                pubs = session.exec(
                    select(PublicationLog).order_by(PublicationLog.published_at.desc()).limit(limit)
                ).all()
                return [
                    {
                        "id": p.id,
                        "draft_id": p.draft_id,
                        "username": p.username,
                        "project": p.project,
                        "bitrix_id": p.bitrix_id,
                        "published_at": p.published_at.isoformat() if p.published_at else None,
                        "image_url": p.image_url,
                        "seo_title": p.seo_title,
                        "url": p.url,
                        "estimated_cost_rub": p.cost_rub,
                    }
                    for p in pubs
                ]
        except Exception as e:
            logger.error(f"Error getting publications: {e}")
            raise

    @staticmethod
    def log_publication(
        draft_id: int,
        username: Optional[str],
        project: Optional[str],
        bitrix_id: Optional[int],
        url: Optional[str],
        image_url: Optional[str],
        seo_title: Optional[str],
        cost_rub: int = 0,
    ) -> int:
        try:
            with DatabaseSession() as session:
                entry = PublicationLog(
                    draft_id=draft_id,
                    username=username,
                    project=project,
                    bitrix_id=bitrix_id,
                    url=url,
                    image_url=image_url,
                    seo_title=seo_title,
                    cost_rub=cost_rub,
                )
                session.add(entry)
                session.commit()
                session.refresh(entry)
                logger.info(f"Logged publication {entry.id} for draft {draft_id}")
                return entry.id
        except Exception as e:
            logger.error(f"Error logging publication: {e}")
            raise
    
    @staticmethod
    def delete_draft(draft_id: int) -> bool:
        """
        Удаление черновика
        
        Args:
            draft_id: ID черновика
            
        Returns:
            bool: Успешность операции
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")
                
                # Удаляем связанные логи
                logs = session.exec(
                    select(GenerationLog).where(GenerationLog.draft_id == draft_id)
                ).all()
                
                for log in logs:
                    session.delete(log)
                
                # Удаляем черновик
                session.delete(draft)
                session.commit()
                
                logger.info(f"Deleted draft {draft_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting draft: {e}")
            raise

    @staticmethod
    def schedule_publication(
        draft_id: int,
        scheduled_at: datetime,
        project_code: str,
        main_type: Optional[int] = None,
        current_user_id: Optional[int] = None
    ) -> bool:
        """
        Планирование публикации статьи
        
        Args:
            draft_id: ID черновика
            scheduled_at: Время публикации (UTC)
            project_code: Код проекта (GS, TS, PS)
            main_type: ID главной нозологии
            current_user_id: ID пользователя
            
        Returns:
            bool: Успешность операции
        """
        try:
            from database.models import NewsStatus
            
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")
                
                # Обновляем статус и время
                draft.status = "scheduled"
                draft.scheduled_at = scheduled_at
                draft.published_project_code = project_code
                
                if current_user_id:
                    draft.created_by = current_user_id
                
                # Сохраняем дополнительные параметры в JSON для использования при публикации
                draft.generated_seo_description = draft.generated_seo_description or ""
                
                session.commit()
                
                logger.info(f"Scheduled publication for draft {draft_id} at {scheduled_at}")
                return True
                
        except Exception as e:
            logger.error(f"Error scheduling publication: {e}")
            raise

    @staticmethod
    def reschedule_publication(draft_id: int, new_scheduled_at: datetime) -> bool:
        """
        Изменение времени отложенной публикации
        
        Args:
            draft_id: ID черновика
            new_scheduled_at: Новое время публикации (UTC)
            
        Returns:
            bool: Успешность операции
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")
                
                draft.scheduled_at = new_scheduled_at
                session.commit()
                
                logger.info(f"Rescheduled publication for draft {draft_id} to {new_scheduled_at}")
                return True
                
        except Exception as e:
            logger.error(f"Error rescheduling publication: {e}")
            raise

    @staticmethod
    def cancel_scheduled_publication(draft_id: int) -> bool:
        """
        Отмена отложенной публикации
        
        Args:
            draft_id: ID черновика
            
        Returns:
            bool: Успешность операции
        """
        try:
            from database.models import NewsStatus
            
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")
                
                draft.status = "generated"
                draft.scheduled_at = None
                session.commit()
                
                logger.info(f"Cancelled scheduled publication for draft {draft_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error cancelling scheduled publication: {e}")
            raise

    @staticmethod
    def get_published_news(filter_obj) -> Dict[str, Any]:
        """
        Получение списка опубликованных и запланированных новостей

        Args:
            filter_obj: Объект с фильтрами

        Returns:
            dict: Список новостей с пагинацией
        """
        try:
            from database.models import User, NewsStatus
            from math import ceil

            with DatabaseSession() as session:
                # Используем старую систему через NewsGenerationDraft
                query = select(
                    NewsGenerationDraft,
                    Article.title.label("article_title"),
                    User.username.label("author_name")
                ).join(
                    Article, NewsGenerationDraft.article_id == Article.id
                ).outerjoin(
                    User, NewsGenerationDraft.created_by == User.id
                ).where(
                    NewsGenerationDraft.status.in_(["scheduled", "published", "generated"])
                )

                # Применяем фильтры
                if filter_obj.project:
                    query = query.where(NewsGenerationDraft.project == filter_obj.project)

                if filter_obj.author:
                    query = query.where(NewsGenerationDraft.created_by == filter_obj.author)

                if filter_obj.date_from:
                    query = query.where(NewsGenerationDraft.published_at >= filter_obj.date_from)

                if filter_obj.date_to:
                    query = query.where(NewsGenerationDraft.published_at <= filter_obj.date_to)

                # Подсчет общего количества
                from sqlmodel import func
                count_query = select(func.count(NewsGenerationDraft.id)).join(
                    Article, NewsGenerationDraft.article_id == Article.id
                ).outerjoin(
                    User, NewsGenerationDraft.created_by == User.id
                ).where(
                    NewsGenerationDraft.status.in_(["scheduled", "published", "generated"])
                )

                # Применяем те же фильтры что и в основном запросе
                if filter_obj.project:
                    count_query = count_query.where(NewsGenerationDraft.project == filter_obj.project)

                if filter_obj.author:
                    count_query = count_query.where(NewsGenerationDraft.created_by == filter_obj.author)

                if filter_obj.date_from:
                    count_query = count_query.where(NewsGenerationDraft.published_at >= filter_obj.date_from)

                if filter_obj.date_to:
                    count_query = count_query.where(NewsGenerationDraft.published_at <= filter_obj.date_to)

                total = session.exec(count_query).one()

                # Сортировка: сначала запланированные (scheduled), затем опубликованные по дате публикации
                from sqlalchemy import case
                query = query.order_by(
                    case(
                        (NewsGenerationDraft.status == "scheduled", 1),
                        (NewsGenerationDraft.status == "published", 2),
                        else_=3
                    ),
                    # Для scheduled сортируем по scheduled_at DESC (ближайшие по времени сверху)
                    # Для published сортируем по published_at DESC (новые публикации сверху)
                    NewsGenerationDraft.scheduled_at.desc().nulls_last(),
                    NewsGenerationDraft.published_at.desc().nulls_last(),
                    NewsGenerationDraft.created_at.desc()
                )

                # Пагинация
                offset = (filter_obj.page - 1) * filter_obj.limit
                query = query.offset(offset).limit(filter_obj.limit)

                results = session.exec(query).all()

                # Определяем название проектов
                project_names = {
                    "gynecology.school": "Gynecology School",
                    "therapy.school": "Therapy School",
                    "pediatrics.school": "Pediatrics School",
                    "GS": "Gynecology School",
                    "TS": "Therapy School",
                    "PS": "Pediatrics School",
                    "TEST": "Test Project",
                    "TEST2": "Test Project 2"
                }

                items = []

                # Используем старую систему через черновики
                for draft, article_title, author_name in results:
                    item = {
                        "id": draft.id,
                        "article_id": draft.article_id,
                        "title": article_title or "Без заголовка",
                        "seo_title": draft.generated_seo_title,
                        "news_text": draft.generated_news_text,
                        "image_url": draft.generated_image_url,
                        "generated_image_url": draft.generated_image_url,
                        "author_name": author_name or "Неизвестно",
                        "status": draft.status,
                        "scheduled_at": draft.scheduled_at,
                        "published_at": draft.published_at,
                        "created_at": draft.created_at,
                        "is_published": draft.status == "published",
                        "is_scheduled": draft.status == "scheduled",
                        "has_draft": True,
                        "published_project_code": draft.published_project_code,
                        "published_project_name": project_names.get(draft.published_project_code, draft.published_project_code) if draft.published_project_code else None,
                        "bitrix_id": draft.bitrix_id,
                        "published_projects": [{
                            "project_code": draft.published_project_code,
                            "project_name": project_names.get(draft.published_project_code, draft.published_project_code),
                            "bitrix_id": draft.bitrix_id,
                            "published_at": draft.published_at
                        }] if draft.published_project_code else []
                    }
                    items.append(item)

                pages = ceil(total / filter_obj.limit) if total > 0 else 1

                return {
                    "items": items,
                    "total": total,
                    "page": filter_obj.page,
                    "pages": pages
                }

        except Exception as e:
            logger.error(f"Error getting published news: {e}")
            raise

    @staticmethod
    def get_scheduled_publications() -> List[int]:
        """
        Получение всех запланированных публикаций, время которых наступило
        
        Returns:
            List[int]: Список ID черновиков готовых к публикации
        """
        try:
            with DatabaseSession() as session:
                now = moscow_now()
                
                query = select(NewsGenerationDraft).where(
                    NewsGenerationDraft.status == "scheduled",
                    NewsGenerationDraft.scheduled_at <= now
                )
                
                results = session.exec(query).all()
                
                # Возвращаем только ID, чтобы избежать проблем с сессиями
                draft_ids = [draft.id for draft in results]
                
                logger.info(f"Found {len(draft_ids)} scheduled publications ready to publish")
                return draft_ids
                
        except Exception as e:
            logger.error(f"Error getting scheduled publications: {e}")
            return []

    @staticmethod
    def mark_draft_error(
        draft_id: int,
        error_message: str,
        error_step: str,
        can_retry: bool = True
    ) -> bool:
        """
        Отметить черновик как имеющий ошибку

        Args:
            draft_id: ID черновика
            error_message: Сообщение об ошибке
            error_step: Шаг, на котором произошла ошибка
            can_retry: Можно ли повторить операцию

        Returns:
            bool: Успешность операции
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")

                # Обновляем информацию об ошибке
                draft.last_error_message = error_message
                draft.last_error_step = error_step
                draft.last_error_at = moscow_now()
                draft.can_retry = can_retry
                draft.retry_count = (draft.retry_count or 0) + 1
                draft.updated_at = moscow_now()

                # Обновляем статус если это критическая ошибка
                if not can_retry:
                    draft.status = "error"

                session.commit()
                logger.info(f"Marked draft {draft_id} with error at step '{error_step}': {error_message}")
                return True

        except Exception as e:
            logger.error(f"Error marking draft error: {e}")
            raise

    @staticmethod
    def clear_draft_error(draft_id: int) -> bool:
        """
        Очистить информацию об ошибке черновика

        Args:
            draft_id: ID черновика

        Returns:
            bool: Успешность операции
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")

                # Очищаем информацию об ошибке
                draft.last_error_message = None
                draft.last_error_step = None
                draft.last_error_at = None
                draft.can_retry = True
                draft.updated_at = moscow_now()

                session.commit()
                logger.info(f"Cleared error info for draft {draft_id}")
                return True

        except Exception as e:
            logger.error(f"Error clearing draft error: {e}")
            raise

    @staticmethod
    def get_failed_drafts(
        limit: int = 50,
        include_recoverable_only: bool = True,
        user_id: Optional[int] = None
    ) -> List[NewsGenerationDraftRead]:
        """
        Получить черновики с ошибками, которые можно восстановить

        Args:
            limit: Максимальное количество результатов
            include_recoverable_only: Включать только восстанавливаемые черновики
            user_id: Фильтр по пользователю (опционально)

        Returns:
            List[NewsGenerationDraftRead]: Список черновиков с ошибками
        """
        try:
            with DatabaseSession() as session:
                query = select(NewsGenerationDraft).where(
                    NewsGenerationDraft.last_error_message.isnot(None)
                )

                if include_recoverable_only:
                    query = query.where(NewsGenerationDraft.can_retry == True)

                if user_id:
                    query = query.where(NewsGenerationDraft.created_by == user_id)

                query = query.order_by(
                    NewsGenerationDraft.last_error_at.desc()
                ).limit(limit)

                drafts = session.exec(query).all()

                return [
                    NewsGenerationDraftRead(
                        id=draft.id,
                        article_id=draft.article_id,
                        project=draft.project,
                        summary=draft.summary,
                        facts=draft.facts,
                        generated_news_text=draft.generated_news_text,
                        generated_seo_title=draft.generated_seo_title,
                        generated_seo_description=draft.generated_seo_description,
                        generated_seo_keywords=draft.generated_seo_keywords,
                        generated_image_prompt=draft.generated_image_prompt,
                        generated_image_url=draft.generated_image_url,
                        status=draft.status,
                        last_error_message=draft.last_error_message,
                        last_error_step=draft.last_error_step,
                        last_error_at=draft.last_error_at,
                        can_retry=draft.can_retry or True,
                        retry_count=draft.retry_count or 0,
                        # Информация о публикации
                        is_published=draft.is_published or False,
                        published_project_code=draft.published_project_code,
                        published_project_name=draft.published_project_name,
                        bitrix_id=draft.bitrix_id,
                        published_at=draft.published_at,
                        created_at=draft.created_at,
                        updated_at=draft.updated_at
                    )
                    for draft in drafts
                ]

        except Exception as e:
            logger.error(f"Error getting failed drafts: {e}")
            raise

    @staticmethod
    def can_retry_draft(draft_id: int) -> bool:
        """
        Проверить, можно ли повторить операцию с черновиком

        Args:
            draft_id: ID черновика

        Returns:
            bool: Можно ли повторить
        """
        try:
            with DatabaseSession() as session:
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    return False

                # Проверяем флаг can_retry и количество попыток
                max_retries = 3  # Максимум 3 попытки
                return (
                    (draft.can_retry or True) and
                    (draft.retry_count or 0) < max_retries and
                    draft.status != "published"
                )

        except Exception as e:
            logger.error(f"Error checking if draft can retry: {e}")
            return False

    @staticmethod
    def delete_draft(draft_id: int) -> bool:
        """
        Удаление черновика и всех связанных данных
        """
        try:
            with DatabaseSession() as session:
                # Получаем черновик
                draft = session.get(NewsGenerationDraft, draft_id)
                if not draft:
                    raise ValueError(f"Черновик с ID {draft_id} не найден")

                # Удаляем связанные логи генерации (если есть)
                from sqlmodel import select
                try:
                    from database.models import GenerationLog
                    logs = session.exec(
                        select(GenerationLog).where(GenerationLog.draft_id == draft_id)
                    ).all()
                    for log in logs:
                        session.delete(log)
                    logger.info(f"Found and will delete {len(logs)} logs for draft {draft_id}")
                except Exception as e:
                    logger.warning(f"Could not delete logs for draft {draft_id}: {e}")

                # Удаляем черновик
                session.delete(draft)
                session.commit()

                logger.info(f"Deleted draft {draft_id} and {len(logs)} related logs")
                return True

        except Exception as e:
            logger.error(f"Error deleting draft {draft_id}: {e}")
            return False


# Глобальный экземпляр сервиса
news_generation_service = NewsGenerationService()