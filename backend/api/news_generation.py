"""
API эндпоинты для генерации новостей
"""

import json
import time
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from database.connection import get_session, DatabaseSession
from database.models import Article, ProjectType, User, NewsGenerationDraft
from database.schemas import (
    ArticleSummaryRequest, ArticleSummary, SummaryConfirmationRequest,
    ArticleGenerationRequest, GeneratedArticleResponse, ArticleDraft,
    RegenerateImageRequest, NewsGenerationDraftRead, GenerationLogRead,
    ArticleFormattingOptions, ArticleFormattingStyle, ArticleParagraphLength
)
from models.schemas import ArticleDraftUpdate, PublishToBitrixRequest, PublishRequest, ScheduleRequest, PublicationMode, PublishedNewsFilter, PublishedNewsResponse
from services.ai_service import get_ai_service
from services.news_generation_service import news_generation_service
from services.bitrix_service import bitrix_service
import httpx
from core.config import settings
from api.expenses import auto_create_expense
from database.models import ExpenseType
from api.dependencies import get_current_user_optional
from io import BytesIO
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_BREAK
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/news-generation", tags=["news-generation"])


@router.post("/summarize", response_model=ArticleSummary)
async def summarize_article(
    request: ArticleSummaryRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Создание выжимки статьи с помощью GPT-3.5
    """
    try:
        # Получаем статью из базы данных
        article = session.get(Article, request.article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Статья не найдена")
        
        # Получаем AI сервис
        ai_service = get_ai_service()
        
        # Засекаем время
        start_time = time.time()
        
        try:
            # Преобразуем строку project в enum (используем БД enum)
            project_enum = ProjectType(request.project)
            
            # Генерируем выжимку
            summary, metrics = await ai_service.summarize_article(
                article_content=article.content,
                article_title=article.title,
                project=project_enum
            )
            
            processing_time = time.time() - start_time
            
            # Создаем черновик синхронно
            draft_id = news_generation_service.create_draft(
                article_id=request.article_id,
                project=project_enum,
                summary=summary.summary,
                facts=summary.facts,
                created_by=(current_user.id if current_user else None)
            )

            # Логируем расход 40 ₽ за выжимку (создание новости)
            try:
                if current_user:
                    # Преобразуем строку проекта в ProjectType
                    project = None
                    if current_user.project:
                        try:
                            # Сначала попробуем как enum value
                            project = ProjectType(current_user.project)
                        except ValueError:
                            try:
                                # Попробуем как enum name (GYNECOLOGY -> ProjectType.GYNECOLOGY)
                                project = ProjectType[current_user.project]
                            except KeyError:
                                logger.warning(f"Unknown project type: {current_user.project}")
                                # Устанавливаем fallback проект
                                project = ProjectType.GYNECOLOGY
                    
                    await auto_create_expense(
                        user_id=current_user.id,
                        project=project,
                        expense_type=ExpenseType.NEWS_CREATION,
                        description=f"Создание выжимки для статьи '{article.title[:50]}...'",
                        related_article_id=article.id,
                        session=session
                    )
            except Exception as e:
                logger.warning(f"Failed to log expense for summary creation: {e}")
            
            # Логируем успешную операцию в фоне
            background_tasks.add_task(
                log_success_background,
                draft_id,
                "summary",
                "gpt-3.5-turbo-16k",
                processing_time,
                metrics.get("tokens_used")
            )

            return ArticleSummary(
                article_id=request.article_id,
                project=request.project,
                summary=summary.summary,
                facts=summary.facts,
                draft_id=draft_id
            )
            
        except Exception as ai_error:
            processing_time = time.time() - start_time

            # Создаем временный черновик для логирования ошибки
            try:
                project_enum_fallback = ProjectType(request.project)
            except Exception:
                project_enum_fallback = ProjectType.THERAPY
            draft_id = news_generation_service.create_draft(
                article_id=request.article_id,
                project=project_enum_fallback,
                summary="",
                facts=[],
                created_by=(current_user.id if 'current_user' in locals() and current_user else None)
            )

            # Отмечаем ошибку в черновике для возможности восстановления
            news_generation_service.mark_draft_error(
                draft_id=draft_id,
                error_message=str(ai_error),
                error_step="summary",
                can_retry=True
            )

            # Логируем ошибку в фоне
            background_tasks.add_task(
                log_error_background_draft,
                draft_id,
                "summary",
                "gpt-3.5-turbo-16k",
                processing_time,
                str(ai_error)
            )

            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при генерации выжимки: {str(ai_error)}. Черновик {draft_id} сохранен для восстановления."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in summarize_article: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/confirm-summary", response_model=Dict[str, Any])
async def confirm_summary(
    request: SummaryConfirmationRequest,
    background_tasks: BackgroundTasks
):
    """
    Подтверждение выжимки и обновление черновика
    """
    try:
        # Обновляем черновик
        success = news_generation_service.update_draft_status(
            draft_id=request.draft_id,
            status="summary_confirmed",
            summary=request.summary,
            facts=request.facts
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Черновик не найден")
        

        return {"success": True, "message": "Выжимка подтверждена", "draft_id": request.draft_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in confirm_summary: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/generate-article", response_model=GeneratedArticleResponse)
async def generate_article(
    request: ArticleGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Генерация полной статьи с SEO (модель задается в настройках, по умолчанию GPT-5-mini)
    """
    try:
        # Получаем черновик
        draft = news_generation_service.get_draft(request.draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Черновик не найден")
        
        if draft.status != "summary_confirmed":
            raise HTTPException(
                status_code=400,
                detail="Выжимка должна быть подтверждена перед генерацией статьи"
            )
        
        # Получаем AI сервис
        ai_service = get_ai_service()
        
        # Засекаем время
        start_time = time.time()
        
        try:
            # Парсим факты из JSON
            facts = json.loads(draft.facts) if draft.facts else []
            
            # Получаем оригинальную статью для заголовка
            from database.connection import DatabaseSession
            from database.models import Article
            with DatabaseSession() as session:
                article = session.get(Article, draft.article_id)
                original_title = article.title if article else "Без заголовка"
            
            # Преобразуем строку project в enum
            project_enum = ProjectType(draft.project)
            
            # Генерируем полную статью
            generated_article, metrics = await ai_service.generate_full_article(
                summary=draft.summary,
                facts=facts,
                project=project_enum,
                original_title=original_title,
                formatting_options=request.formatting_options
            )
            
            processing_time = time.time() - start_time
            
            # Сохраняем сгенерированный контент
            news_generation_service.save_generated_content(
                draft_id=request.draft_id,
                generated_content={
                    "news_text": generated_article.news_text,
                    "seo_title": generated_article.seo_title,
                    "seo_description": generated_article.seo_description,
                    "seo_keywords": generated_article.seo_keywords,
                    "image_prompt": generated_article.image_prompt,
                    "image_url": generated_article.image_url
                }
            )
            
            # Логируем успешную операцию в фоне
            background_tasks.add_task(
                log_success_background,
                request.draft_id,
                "generation",
                metrics.get("model_used", "gpt-4o"),
                processing_time,
                metrics.get("tokens_used")
            )
            
            return GeneratedArticleResponse(
                draft_id=request.draft_id,
                news_text=generated_article.news_text,
                seo_title=generated_article.seo_title,
                seo_description=generated_article.seo_description,
                seo_keywords=generated_article.seo_keywords,
                image_prompt=generated_article.image_prompt,
                image_url=generated_article.image_url
            )
            
        except Exception as ai_error:
            processing_time = time.time() - start_time

            # Отмечаем ошибку в черновике для возможности восстановления
            news_generation_service.mark_draft_error(
                draft_id=request.draft_id,
                error_message=str(ai_error),
                error_step="generation",
                can_retry=True
            )

            # Логируем ошибку в фоне
            background_tasks.add_task(
                log_error_background_draft,
                request.draft_id,
                "generation",
                "gpt-4o",
                processing_time,
                str(ai_error)
            )

            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при генерации статьи: {str(ai_error)}. Черновик {request.draft_id} сохранен для восстановления."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_article: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/regenerate-image", response_model=Dict[str, str])
async def regenerate_image(
    request: RegenerateImageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_optional),
    session: Session = Depends(get_session)
):
    """
    Перегенерация изображения для статьи
    """
    try:
        # Получаем черновик
        draft = news_generation_service.get_draft(request.draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Черновик не найден")
        
        # Получаем AI сервис
        ai_service = get_ai_service()
        
        # Засекаем время
        start_time = time.time()
        
        try:
            # Генерируем новое изображение
            new_image_url, metrics = await ai_service.regenerate_image(request.new_prompt)
            
            processing_time = time.time() - start_time
            
            # Обновляем URL изображения в черновике
            news_generation_service.update_image_url(
                draft_id=request.draft_id,
                new_image_url=new_image_url,
                new_prompt=request.new_prompt
            )
            
            # Логируем успешную операцию в фоне
            background_tasks.add_task(
                log_success_background,
                request.draft_id,
                "image_regeneration",
                "yandex-art",
                processing_time
            )
            
            # Логируем расход 10 ₽ за перегенерацию фото
            try:
                if current_user:
                    # Преобразуем строку проекта в ProjectType
                    project = None
                    if current_user.project:
                        try:
                            # Сначала попробуем как enum value
                            project = ProjectType(current_user.project)
                        except ValueError:
                            try:
                                # Попробуем как enum name (GYNECOLOGY -> ProjectType.GYNECOLOGY)
                                project = ProjectType[current_user.project]
                            except KeyError:
                                logger.warning(f"Unknown project type: {current_user.project}")
                                # Устанавливаем fallback проект
                                project = ProjectType.GYNECOLOGY
                    
                    logger.info(f"Creating expense for image regeneration: user={current_user.username}, project={project}")
                    
                    await auto_create_expense(
                        user_id=current_user.id,
                        project=project,
                        expense_type=ExpenseType.PHOTO_REGENERATION,
                        description=f"Перегенерация изображения для черновика {request.draft_id}",
                        related_article_id=draft.article_id,  # Используем article_id из черновика
                        session=session
                    )
                else:
                    logger.warning("No current_user for expense logging in image regeneration")
            except Exception as e:
                logger.error(f"Failed to log expense for image regeneration: {e}")
                import traceback
                traceback.print_exc()

            return {
                "image_url": new_image_url,
                "prompt": request.new_prompt
            }
            
        except Exception as ai_error:
            processing_time = time.time() - start_time
            
            # Логируем ошибку в фоне
            background_tasks.add_task(
                log_error_background_draft,
                request.draft_id,
                "image_regeneration",
                "yandex-art",
                processing_time,
                str(ai_error)
            )
            
            # Вместо ошибки возвращаем fallback изображение
            fallback_image_url = "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?ixlib=rb-4.0.3&auto=format&fit=crop&w=1024&h=1024&q=80"
            
            # Обновляем URL изображения в черновике
            news_generation_service.update_image_url(
                draft_id=request.draft_id,
                new_image_url=fallback_image_url,
                new_prompt=request.new_prompt
            )
            
            return {
                "image_url": fallback_image_url,
                "prompt": request.new_prompt
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in regenerate_image: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/drafts", response_model=List[NewsGenerationDraftRead])
async def get_drafts(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    article_id: Optional[int] = None
):
    """
    Получение списка черновиков
    """
    try:
        if article_id:
            drafts = news_generation_service.get_drafts_by_article(article_id)
        else:
            drafts = news_generation_service.get_all_drafts(limit, offset, status)
        
        return drafts
        
    except Exception as e:
        logger.error(f"Error in get_drafts: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/drafts/{draft_id}", response_model=NewsGenerationDraftRead)
async def get_draft(draft_id: int):
    """
    Получение черновика по ID
    """
    try:
        draft = news_generation_service.get_draft(draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Черновик не найден")

        return draft

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_draft: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/drafts/by-article/{article_id}", response_model=NewsGenerationDraftRead)
async def get_draft_by_article(
    article_id: int,
    project: str = Query(..., description="Тип проекта (gynecology.school, therapy.school, etc.)")
):
    """
    Получение черновика по ID статьи и проекту
    """
    try:
        draft = news_generation_service.get_draft_by_article_and_project(article_id, project)
        if not draft:
            raise HTTPException(status_code=404, detail="Черновик не найден")

        return draft

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_draft_by_article: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.delete("/drafts/{draft_id}")
async def delete_draft(draft_id: int):
    """
    Удаление черновика
    """
    try:
        success = news_generation_service.delete_draft(draft_id)
        if success:
            return {"success": True, "message": "Черновик успешно удален"}
        else:
            raise HTTPException(status_code=404, detail="Черновик не найден")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting draft {draft_id}: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


def convert_markdown_to_html(text: str) -> str:
    """Конвертирует простую markdown разметку в HTML для Telegram"""
    import re

    # Конвертируем **жирный** и *жирный* в <b>жирный</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<b>\1</b>', text)

    # Конвертируем _курсив_ в <i>курсив</i>
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)

    # Конвертируем `код` в <code>код</code>
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)

    return text


async def send_to_telegram(text: str, photo_url: Optional[str] = None) -> None:
    """Отправка сообщения в Telegram-канал (текст или фото с подписью).

    Если photo_url недоступен публично (например, localhost), пробуем скачать байты и загрузить файл.
    """
    try:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        if not token or not chat_id:
            raise RuntimeError("TELEGRAM_BOT_TOKEN/CHAT_ID не настроены")

        # Конвертируем markdown в HTML для корректного отображения в Telegram
        formatted_text = convert_markdown_to_html(text)

        async with httpx.AsyncClient(timeout=20.0) as client:
            if photo_url:
                # Пытаемся загрузить фото по URL и отправить как файл (надёжнее, чем отдавать URL)
                try:
                    # Изображения теперь генерируются и хранятся в том же backend сервисе
                    fetch_url = photo_url
                    try:
                        from urllib.parse import urlparse, urlunparse
                        parts = urlparse(photo_url)
                        # Обновленная логика для локального доступа
                        if parts.hostname in ("localhost", "127.0.0.1") and parts.port == 8000:
                            # Используем localhost для доступа к собственным ресурсам
                            fetch_url = photo_url
                    except Exception:
                        fetch_url = photo_url

                    img_resp = await client.get(fetch_url)
                    if img_resp.status_code == 200:
                        img_bytes = img_resp.content
                        url = f"https://api.telegram.org/bot{token}/sendPhoto"
                        files = {"photo": ("image.jpg", img_bytes, "image/jpeg")}
                        data = {"chat_id": chat_id, "caption": formatted_text, "parse_mode": "HTML"}
                        await client.post(url, data=data, files=files)
                    else:
                        # Фолбэк: пробуем передать как ссылку
                        url = f"https://api.telegram.org/bot{token}/sendPhoto"
                        payload = {"chat_id": chat_id, "photo": photo_url, "caption": formatted_text, "parse_mode": "HTML"}
                        await client.post(url, data=payload)
                except Exception:
                    # Фолбэк: отправляем как ссылку
                    url = f"https://api.telegram.org/bot{token}/sendPhoto"
                    payload = {"chat_id": chat_id, "photo": photo_url, "caption": formatted_text, "parse_mode": "HTML"}
                    await client.post(url, data=payload)
            else:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                payload = {"chat_id": chat_id, "text": formatted_text, "parse_mode": "HTML", "disable_web_page_preview": False}
                await client.post(url, json=payload)
    except Exception as e:
        logger.error(f"Error sending message to Telegram: {e}")

@router.put("/drafts/{draft_id}", response_model=Dict[str, Any])
async def update_draft(
    draft_id: int,
    draft_data: ArticleDraftUpdate
):
    """
    Обновление черновика (для редактирования)
    """
    try:
        # Логируем входящие данные от фронтенда
        logger.info(f"[DEBUG] update_draft: draft_id={draft_id}")
        logger.info(f"[DEBUG] news_text from frontend: {repr(draft_data.news_text[:300])}")
        
        # Получаем текущий черновик
        current_draft = news_generation_service.get_draft(draft_id)
        if not current_draft:
            raise HTTPException(status_code=404, detail="Черновик не найден")
        
        # Обновляем содержимое
        generated_content = {
            "news_text": draft_data.news_text,
            "seo_title": draft_data.seo_title,
            "seo_description": draft_data.seo_description,
            "seo_keywords": draft_data.seo_keywords,
            "image_prompt": draft_data.image_prompt,
            "image_url": draft_data.image_url
        }
        
        logger.info(f"[DEBUG] Generated content news_text: {repr(generated_content['news_text'][:300])}")
        
        success = news_generation_service.save_generated_content(
            draft_id=draft_id,
            generated_content=generated_content
        )

        if not success:
            raise HTTPException(status_code=500, detail="Ошибка при обновлении черновика")

        # Обновляем время публикации, если передано
        if draft_data.scheduled_at is not None:
            news_generation_service.update_scheduled_time(draft_id, draft_data.scheduled_at)
        
        # Возвращаем обновленные данные в формате, ожидаемом фронтендом
        return {
            "draft_id": draft_id,
            "news_text": draft_data.news_text,
            "seo_title": draft_data.seo_title,
            "seo_description": draft_data.seo_description,
            "seo_keywords": draft_data.seo_keywords,
            "image_prompt": draft_data.image_prompt,
            "image_url": draft_data.image_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_draft: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.delete("/drafts/{draft_id}", response_model=Dict[str, Any])
async def delete_draft(draft_id: int):
    """
    Удаление черновика
    """
    try:
        success = news_generation_service.delete_draft(draft_id)
        if not success:
            raise HTTPException(status_code=404, detail="Черновик не найден")
        
        return {
            "success": True,
            "message": "Черновик удален"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_draft: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/logs", response_model=List[GenerationLogRead])
async def get_generation_logs(
    draft_id: Optional[int] = None,
    limit: int = 50
):
    """
    Получение логов генерации
    """
    try:
        logs = news_generation_service.get_generation_logs(draft_id, limit)
        return logs
        
    except Exception as e:
        logger.error(f"Error in get_generation_logs: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


# Старый endpoint expenses/summary удален - используйте /api/expenses/summary


@router.get("/publications")
async def get_publications(limit: int = 100):
    """Список публикаций для дашборда аналитика."""
    try:
        items = news_generation_service.get_publications(limit=limit)
        # Обогащаем публикации пользователем и рассчитанной стоимостью по связанным транзакциям
        enriched = []
        for p in items:
            draft_id = p.get("draft_id")
            estimated = news_generation_service.get_expense_total_for_draft(draft_id) if draft_id else 0
            p["estimated_cost_rub"] = estimated
            # если username пуст, подставим 'unknown' для фронта
            if not p.get("username"):
                p["username"] = "unknown"
            enriched.append(p)
        return {"items": enriched}
    except Exception as e:
        logger.error(f"Error in get_publications: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/publish-to-bitrix", response_model=Dict[str, Any])
async def publish_to_bitrix(
    request: PublishToBitrixRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_optional)
):
    """
    Публикация готовой статьи в Bitrix CMS
    """
    try:
        # Получаем черновик
        draft = news_generation_service.get_draft(request.draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Черновик не найден")
        
        if draft.status != "generated":
            raise HTTPException(
                status_code=400,
                detail="Статья должна быть сгенерирована перед публикацией"
            )
        
        # Проверяем что контент сгенерирован
        if not draft.generated_news_text:
            raise HTTPException(
                status_code=400,
                detail="Сгенерированный контент не найден"
            )
        
        # Формируем контент из полей черновика
        generated_content = {
            "news_text": draft.generated_news_text,
            "seo_title": draft.generated_seo_title,
            "seo_description": draft.generated_seo_description,
            "seo_keywords": json.loads(draft.generated_seo_keywords) if draft.generated_seo_keywords else [],
            "image_prompt": draft.generated_image_prompt,
            "image_url": draft.generated_image_url
        }
        
        logger.info(f"[DEBUG] publish_to_bitrix: news_text from DB: {repr(generated_content['news_text'][:300])}")
        
        # Получаем оригинальную статью для источника
        from database.connection import DatabaseSession
        from database.models import Article
        with DatabaseSession() as session:
            article = session.get(Article, draft.article_id)
            original_url = article.url if article else None
        
        # Засекаем время
        start_time = time.time()
        
        try:
            # Публикуем в Bitrix
            # Зафиксируем автора черновика, если он ещё не сохранён
            try:
                if current_user:
                    with DatabaseSession() as s_auth:
                        draft_for_author = s_auth.get(NewsGenerationDraft, request.draft_id)
                        if draft_for_author and not getattr(draft_for_author, "created_by", None):
                            draft_for_author.created_by = current_user.id
                            s_auth.commit()
            except Exception as e:
                logger.warning(f"Failed to set created_by for draft {request.draft_id}: {e}")

            # Публикация
            result = await bitrix_service.publish_article(
                title=generated_content.get("seo_title", ""),
                preview_text=generated_content.get("seo_description", ""),
                detail_text=generated_content.get("news_text", ""),
                project_code=request.project_code,
                source=None,  # Не передаем источник
                main_type=request.main_type,
                image_url=generated_content.get("image_url"),
                seo_title=generated_content.get("seo_title", ""),
                seo_description=generated_content.get("seo_description", ""),
                seo_keywords=", ".join(generated_content.get("seo_keywords", []))
            )
            
            processing_time = time.time() - start_time
            
            if result["success"]:
                # Обновляем информацию о публикации
                news_generation_service.update_publication_info(
                    draft_id=request.draft_id,
                    project_code=request.project_code,
                    project_name=result.get("project", "Неизвестный проект"),
                    bitrix_id=result.get("bitrix_id")
                )

                
                # Лог публикации для аналитики
                try:
                    draft2 = news_generation_service.get_draft(request.draft_id)
                    news_generation_service.log_publication(
                        draft_id=request.draft_id,
                        username=(current_user.username if current_user else None),
                        project=result.get('project'),
                        bitrix_id=result.get('bitrix_id'),
                        url=result.get('url'),
                        image_url=getattr(draft2, 'generated_image_url', None),
                        seo_title=getattr(draft2, 'generated_seo_title', None),
                        cost_rub=news_generation_service.get_expense_total_for_draft(request.draft_id),
                    )
                except Exception as e:
                    logger.error(f"Failed to log publication: {e}")

                # Логируем успешную публикацию в фоне
                background_tasks.add_task(
                    log_success_background,
                    request.draft_id,
                    "publication",
                    "bitrix_cms",
                    processing_time
                )
                
                return {
                    "success": True,
                    "message": "Статья успешно опубликована в Bitrix",
                    "bitrix_id": result.get("bitrix_id"),
                    "project": result.get("project"),
                    "draft_id": request.draft_id,
                    "url": result.get("url")
                }
            else:
                # Отмечаем ошибку в черновике для возможности восстановления
                news_generation_service.mark_draft_error(
                    draft_id=request.draft_id,
                    error_message=result.get("error", "Unknown error"),
                    error_step="publication",
                    can_retry=True
                )

                # Логируем ошибку в фоне
                background_tasks.add_task(
                    log_error_background_draft,
                    request.draft_id,
                    "publication",
                    "bitrix_cms",
                    processing_time,
                    result.get("error", "Unknown error")
                )

                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка публикации в Bitrix: {result.get('error')}. Черновик {request.draft_id} сохранен для восстановления."
                )
                
        except Exception as bitrix_error:
            processing_time = time.time() - start_time

            # Отмечаем ошибку в черновике для возможности восстановления
            news_generation_service.mark_draft_error(
                draft_id=request.draft_id,
                error_message=str(bitrix_error),
                error_step="publication",
                can_retry=True
            )

            # Логируем ошибку в фоне
            background_tasks.add_task(
                log_error_background_draft,
                request.draft_id,
                "publication",
                "bitrix_cms",
                processing_time,
                str(bitrix_error)
            )

            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при публикации в Bitrix: {str(bitrix_error)}. Черновик {request.draft_id} сохранен для восстановления."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in publish_to_bitrix: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/publish", response_model=Dict[str, Any])
async def publish_news(
    request: PublishRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_optional)
):
    """
    Публикация новости с поддержкой отложенной публикации
    """
    try:
        from database.models import NewsStatus
        from datetime import datetime, timezone
        
        # Получаем черновик
        draft = news_generation_service.get_draft(request.draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Черновик не найден")
        
        if draft.status != "generated":
            raise HTTPException(
                status_code=400,
                detail="Статья должна быть сгенерирована перед публикацией"
            )
        
        # Проверяем что контент сгенерирован
        if not draft.generated_news_text:
            raise HTTPException(
                status_code=400,
                detail="Сгенерированный контент не найден"
            )
        
        # Валидации для отложенной публикации
        if request.mode == PublicationMode.LATER:
            if not request.scheduled_at:
                raise HTTPException(
                    status_code=400,
                    detail="Для отложенной публикации необходимо указать время"
                )
            
            # Проверяем что время в будущем
            if request.scheduled_at <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=400,
                    detail="Время публикации должно быть в будущем"
                )
        
        if request.mode == PublicationMode.NOW:
            # Публикуем сейчас - используем существующую логику
            bitrix_request = PublishToBitrixRequest(
                draft_id=request.draft_id,
                project_code=request.project_code,
                main_type=request.main_type
            )
            result = await publish_to_bitrix(bitrix_request, background_tasks, current_user)
            return result
        
        else:  # PublicationMode.LATER
            # Планируем публикацию
            news_generation_service.schedule_publication(
                draft_id=request.draft_id,
                scheduled_at=request.scheduled_at,
                project_code=request.project_code,
                main_type=request.main_type,
                current_user_id=current_user.id if current_user else None
            )
            
            return {
                "success": True,
                "message": "Публикация запланирована",
                "scheduled_at": request.scheduled_at.isoformat(),
                "draft_id": request.draft_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in publish_news: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.patch("/schedule", response_model=Dict[str, Any])
async def reschedule_publication(
    request: ScheduleRequest,
    current_user: User = Depends(get_current_user_optional)
):
    """
    Изменение времени отложенной публикации
    """
    try:
        from datetime import datetime, timezone
        
        # Проверяем что время в будущем
        if request.scheduled_at <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail="Время публикации должно быть в будущем"
            )
        
        # Получаем черновик
        draft = news_generation_service.get_draft(request.draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Черновик не найден")
        
        if draft.status != "scheduled":
            raise HTTPException(
                status_code=400,
                detail="Можно изменить время только для запланированных публикаций"
            )
        
        # Обновляем время
        news_generation_service.reschedule_publication(
            draft_id=request.draft_id,
            new_scheduled_at=request.scheduled_at
        )
        
        return {
            "success": True,
            "message": "Время публикации обновлено",
            "scheduled_at": request.scheduled_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reschedule_publication: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.delete("/schedule/{draft_id}", response_model=Dict[str, Any])
async def cancel_scheduled_publication(
    draft_id: int,
    current_user: User = Depends(get_current_user_optional)
):
    """
    Отмена отложенной публикации
    """
    try:
        # Получаем черновик
        draft = news_generation_service.get_draft(draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Черновик не найден")
        
        if draft.status != "scheduled":
            raise HTTPException(
                status_code=400,
                detail="Можно отменить только запланированные публикации"
            )
        
        # Отменяем публикацию
        news_generation_service.cancel_scheduled_publication(draft_id)
        
        return {
            "success": True,
            "message": "Публикация отменена"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in cancel_scheduled_publication: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/published")
async def get_published_news(
    project: Optional[str] = None,
    status: Optional[str] = None,
    author: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """
    Получение списка опубликованных и запланированных новостей
    """
    try:
        from datetime import datetime
        
        # Преобразуем строки дат в datetime
        parsed_date_from = None
        parsed_date_to = None
        
        if date_from:
            try:
                parsed_date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Неверный формат date_from")
        
        if date_to:
            try:
                parsed_date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Неверный формат date_to")
        
        # Создаем фильтр
        filter_obj = PublishedNewsFilter(
            project=project,
            status=status,
            author=author,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            page=page,
            limit=limit
        )
        
        # Получаем данные
        result = news_generation_service.get_published_news(filter_obj)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_published_news: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/published/{draft_id}", response_model=Dict[str, Any])
async def get_published_article_content(draft_id: int):
    """
    Получение содержимого опубликованной статьи для предварительного просмотра
    """
    try:
        # Получаем черновик
        draft = news_generation_service.get_draft(draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Черновик не найден")

        # Проверяем, что статья была опубликована
        if not draft.is_published:
            raise HTTPException(status_code=400, detail="Статья не была опубликована")

        # Возвращаем полное содержимое
        return {
            "success": True,
            "draft_id": draft.id,
            "title": draft.generated_seo_title or "Без заголовка",
            "content": draft.generated_news_text or "",
            "seo_description": draft.generated_seo_description or "",
            "published_at": draft.published_at,
            "published_project": draft.published_project_name,
            "bitrix_id": draft.bitrix_id,
            "image_url": draft.generated_image_url
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting published article content for draft {draft_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения содержимого статьи")


@router.get("/bitrix-projects", response_model=Dict[str, Any])
async def get_bitrix_projects():
    """
    Получение списка доступных проектов Bitrix для публикации
    """
    try:
        projects = bitrix_service.get_available_projects()
        return {
            "success": True,
            "projects": projects
        }
    except Exception as e:
        logger.error(f"Error getting Bitrix projects: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка проектов")


@router.get("/failed-drafts", response_model=List[NewsGenerationDraftRead])
async def get_failed_drafts(
    limit: int = 50,
    include_recoverable_only: bool = True,
    current_user: User = Depends(get_current_user_optional)
):
    """
    Получение черновиков с ошибками, которые можно восстановить
    """
    try:
        user_id = current_user.id if current_user else None
        failed_drafts = news_generation_service.get_failed_drafts(
            limit=limit,
            include_recoverable_only=include_recoverable_only,
            user_id=user_id
        )

        return failed_drafts

    except Exception as e:
        logger.error(f"Error getting failed drafts: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/retry/{draft_id}", response_model=Dict[str, Any])
async def retry_draft_operation(
    draft_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_optional),
    session: Session = Depends(get_session)
):
    """
    Повторная попытка операции с черновиком после ошибки
    """
    try:
        # Проверяем возможность повтора
        if not news_generation_service.can_retry_draft(draft_id):
            raise HTTPException(
                status_code=400,
                detail="Операция с черновиком не может быть повторена"
            )

        # Получаем черновик
        draft = news_generation_service.get_draft(draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Черновик не найден")

        # Очищаем предыдущую ошибку
        news_generation_service.clear_draft_error(draft_id)

        # Определяем, на каком шаге нужно продолжить
        if draft.last_error_step == "summary":
            # Повторяем создание выжимки
            from database.schemas import ArticleSummaryRequest
            request = ArticleSummaryRequest(
                article_id=draft.article_id,
                project=draft.project
            )
            return await summarize_article(request, background_tasks, session, current_user)

        elif draft.last_error_step == "generation":
            # Повторяем генерацию полной статьи
            from database.schemas import ArticleGenerationRequest
            request = ArticleGenerationRequest(draft_id=draft_id)
            return await generate_article(request, background_tasks)

        elif draft.last_error_step == "publication":
            # Пытаемся повторить публикацию
            return {
                "success": True,
                "message": "Черновик готов к повторной публикации",
                "draft_id": draft_id,
                "next_step": "publication"
            }

        else:
            # Общий случай - возвращаем черновик для ручного продолжения
            return {
                "success": True,
                "message": "Черновик восстановлен",
                "draft_id": draft_id,
                "status": draft.status
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying draft operation: {e}")
        # Отмечаем неудачную попытку
        try:
            news_generation_service.mark_draft_error(
                draft_id,
                str(e),
                "retry",
                can_retry=True
            )
        except:
            pass
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/mark-error/{draft_id}", response_model=Dict[str, Any])
async def mark_draft_error(
    draft_id: int,
    error_message: str,
    error_step: str,
    can_retry: bool = True
):
    """
    Отметить черновик как имеющий ошибку (для внутреннего использования)
    """
    try:
        success = news_generation_service.mark_draft_error(
            draft_id=draft_id,
            error_message=error_message,
            error_step=error_step,
            can_retry=can_retry
        )

        if not success:
            raise HTTPException(status_code=404, detail="Черновик не найден")

        return {
            "success": True,
            "message": "Ошибка черновика зафиксирована"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking draft error: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.delete("/clear-error/{draft_id}", response_model=Dict[str, Any])
async def clear_draft_error(draft_id: int):
    """
    Очистить информацию об ошибке черновика
    """
    try:
        success = news_generation_service.clear_draft_error(draft_id)

        if not success:
            raise HTTPException(status_code=404, detail="Черновик не найден")

        return {
            "success": True,
            "message": "Информация об ошибке очищена"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing draft error: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


from pydantic import BaseModel
from typing import Optional

class TelegramPostSettings(BaseModel):
    hook_type: str = "question"  # question, shocking_fact, statistics, contradiction
    disclosure_level: str = "hint"  # hint, main_idea, almost_all
    call_to_action: str = "curiosity"  # curiosity, urgency, expertise
    includeImage: bool = True

class TelegramPostRequest(BaseModel):
    settings: Optional[TelegramPostSettings] = None

@router.post("/generate-telegram-post/{draft_id}", response_model=Dict[str, Any])
async def generate_telegram_post(
    draft_id: int,
    background_tasks: BackgroundTasks,
    request: Optional[TelegramPostRequest] = None,
    current_user: User = Depends(get_current_user_optional)
):
    """
    Генерация Telegram поста на основе выжимки статьи
    """
    try:
        # Получаем черновик
        draft = news_generation_service.get_draft(draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="Черновик не найден")

        if not draft.summary:
            raise HTTPException(status_code=400, detail="Выжимка не найдена")

        # Получаем AI сервис
        ai_service = get_ai_service()

        # Засекаем время
        start_time = time.time()

        try:
            # Получаем данные оригинальной статьи
            from database.connection import DatabaseSession
            from database.models import Article
            with DatabaseSession() as session:
                article = session.get(Article, draft.article_id)
                article_title = article.title if article else "Без заголовка"
                # На этапе создания поста ссылки на публикацию ещё нет
                article_url = None

            # Парсим факты из JSON
            facts = json.loads(draft.facts) if draft.facts else []

            # Получаем настройки поста
            settings = request.settings if request else TelegramPostSettings()

            # Генерируем Telegram пост с настройками
            tg_post, metrics = await ai_service.generate_telegram_post(
                article_title=article_title,
                article_url=None,  # Для интриги не нужна ссылка в генерации
                summary=draft.summary,
                facts=facts,
                project=ProjectType(draft.project),
                settings=settings
            )

            processing_time = time.time() - start_time

            # Сохраняем пост в черновик
            news_generation_service.save_telegram_post(draft_id, tg_post)

            # Логируем успешную операцию в фоне
            background_tasks.add_task(
                log_success_background,
                draft_id,
                "telegram_post",
                metrics.get("model_used", "gpt-4o-mini"),
                processing_time,
                metrics.get("tokens_used")
            )

            return {
                "success": True,
                "telegram_post": tg_post,
                "processing_time": processing_time
            }

        except Exception as ai_error:
            processing_time = time.time() - start_time

            # Логируем ошибку в фоне
            background_tasks.add_task(
                log_error_background_draft,
                draft_id,
                "telegram_post",
                "gpt-4o-mini",
                processing_time,
                str(ai_error)
            )

            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при генерации Telegram поста: {str(ai_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_telegram_post: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")




# Фоновые задачи для логирования







async def log_error_background_draft(
    draft_id: int,
    operation_type: str,
    model_used: str,
    processing_time: float,
    error_message: str
):
    """Логирование ошибки для существующего черновика в фоне"""
    try:
        news_generation_service.log_generation_operation(
            draft_id=draft_id,
            operation_type=operation_type,
            model_used=model_used,
            success=False,
            processing_time_seconds=processing_time,
            error_message=error_message
        )
        
    except Exception as e:
        logger.error(f"Error in log_error_background_draft: {e}")


async def log_success_background(
    draft_id: int,
    operation_type: str,
    model_used: str,
    processing_time: float,
    tokens_used: Optional[int] = None
):
    """Логирование успешной операции в фоне"""
    try:
        news_generation_service.log_generation_operation(
            draft_id=draft_id,
            operation_type=operation_type,
            model_used=model_used,
            success=True,
            processing_time_seconds=processing_time,
            tokens_used=tokens_used
        )
        
    except Exception as e:
        logger.error(f"Error in log_success_background: {e}")