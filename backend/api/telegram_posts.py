"""
API эндпоинты для работы с Telegram постами опубликованных новостей
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlmodel import Session, select

from database.connection import get_session
from database.models import (
    TelegramPost, TelegramPostRead, TelegramPostCreate, TelegramPostSettings,
    NewsGenerationDraft, User, ExpenseType, ProjectType
)
from pydantic import BaseModel
from api.dependencies import get_current_user_optional
from services.ai_service import get_ai_service
from api.news_generation import send_to_telegram
from api.expenses import auto_create_expense

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram-posts", tags=["telegram-posts"])


class TelegramPublishRequest(BaseModel):
    """Запрос на публикацию поста в Telegram"""
    post_text: str
    article_url: Optional[str] = None
    link_button_text: str = "📖 Читать полную статью"


@router.get("/news/{news_draft_id}", response_model=List[TelegramPostRead])
async def get_telegram_posts_for_news(
    news_draft_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Получить все Telegram посты для конкретной опубликованной новости
    """
    # Проверяем, что новость существует
    news_draft = session.get(NewsGenerationDraft, news_draft_id)
    if not news_draft:
        raise HTTPException(status_code=404, detail="Новость не найдена")

    # Для неопубликованных новостей возвращаем пустой массив вместо ошибки
    if not news_draft.is_published:
        return []

    # Получаем все Telegram посты для этой новости
    statement = select(TelegramPost).where(TelegramPost.news_draft_id == news_draft_id)
    telegram_posts = session.exec(statement).all()

    return telegram_posts


@router.post("/news/{news_draft_id}", response_model=TelegramPostRead)
async def create_telegram_post(
    news_draft_id: int,
    settings: TelegramPostSettings,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Создать новый Telegram пост для опубликованной новости
    """
    # Проверяем, что новость существует
    news_draft = session.get(NewsGenerationDraft, news_draft_id)
    if not news_draft:
        raise HTTPException(status_code=404, detail="Новость не найдена")

    # Для создания поста новость должна быть опубликована
    if not news_draft.is_published:
        raise HTTPException(status_code=400, detail="Новость еще не опубликована")

    # Получаем оригинальную статью для генерации
    from database.models import Article
    article = session.get(Article, news_draft.article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Оригинальная статья не найдена")

    try:
        # Генерируем Telegram пост с помощью AI
        ai_service = get_ai_service()

        # Используем URL из настроек или формируем автоматически
        published_url = settings.article_url

        if not published_url and news_draft.bitrix_id:
            # Формируем правильные URL для каждого проекта
            # TODO: В будущем заменить на реальные URL, сохранённые из Bitrix API
            project_urls = {
                "gynecology.school": f"https://gynecology.school/content/articles/news/{news_draft.bitrix_id}/",
                "therapy.school": f"https://therapy.school/content/articles/news/{news_draft.bitrix_id}/",
                "pediatrics.school": f"https://pediatrics.school/content/articles/news/{news_draft.bitrix_id}/"
            }
            published_url = project_urls.get(news_draft.project)

        # Подготавливаем данные новости для AI
        news_data = {
            "seo_title": news_draft.generated_seo_title or article.title,
            "news_text": news_draft.generated_news_text or article.content,
            "image_url": news_draft.generated_image_url,
            "project": news_draft.project,
            "published_url": published_url
        }

        # Создаем настройки для AI
        from services.ai_service import TelegramPostSettings
        ai_settings = TelegramPostSettings(
            hook_type=settings.hook_type,
            disclosure_level=settings.disclosure_level,
            call_to_action=settings.call_to_action,
            includeImage=settings.include_image  # Сохраняем старое название для совместимости
        )

        # Генерируем пост с использованием нового метода
        post_text, metrics = await ai_service.generate_telegram_post_for_published(
            news_data=news_data,
            settings=ai_settings
        )

        # Создаем запись в БД
        telegram_post = TelegramPost(
            news_draft_id=news_draft_id,
            hook_type=settings.hook_type,
            disclosure_level=settings.disclosure_level,
            call_to_action=settings.call_to_action,
            include_image=settings.include_image,
            post_text=post_text,
            character_count=len(post_text),
            is_published=False,  # Явно устанавливаем значение по умолчанию
            created_by=current_user.id if current_user else None
        )

        session.add(telegram_post)
        session.commit()
        session.refresh(telegram_post)
        
        # Логируем для отладки
        logger.info(f"Created telegram post: id={telegram_post.id}, news_id={news_draft_id}")
        logger.info(f"Telegram post fields: hook_type={telegram_post.hook_type}, is_published={telegram_post.is_published}, created_at={telegram_post.created_at}")

        # Создаем расход за создание Telegram поста
        if current_user:
            try:
                # Определяем проект пользователя
                project_type = None
                if news_draft.project:
                    try:
                        project_type = ProjectType(news_draft.project)
                    except ValueError:
                        # Если не удалось привести к enum, используем проект пользователя
                        if current_user.project:
                            try:
                                project_type = ProjectType(current_user.project)
                            except ValueError:
                                project_type = ProjectType.THERAPY  # fallback
                        else:
                            project_type = ProjectType.THERAPY  # fallback

                # Создаем расход
                await auto_create_expense(
                    user_id=current_user.id,
                    project=project_type,
                    expense_type=ExpenseType.TELEGRAM_POST,
                    description=f"Создание Telegram поста для статьи ID: {news_draft.article_id}",
                    related_article_id=news_draft.article_id,
                    session=session
                )
                logger.info(f"Created expense for Telegram post creation: user={current_user.id}, article={news_draft.article_id}")
            except Exception as expense_error:
                # Логируем ошибку создания расхода, но не прерываем процесс создания поста
                logger.error(f"Failed to create expense for Telegram post creation: {expense_error}")

        # Финальная проверка объекта перед возвратом
        logger.info(f"Returning telegram post: {telegram_post}")
        logger.info(f"Post fields before return: id={getattr(telegram_post, 'id', 'MISSING')}, created_at={getattr(telegram_post, 'created_at', 'MISSING')}, updated_at={getattr(telegram_post, 'updated_at', 'MISSING')}")
        
        return telegram_post

    except Exception as e:
        logger.error(f"Ошибка при генерации Telegram поста: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации поста: {str(e)}")


@router.put("/{post_id}", response_model=TelegramPostRead)
async def update_telegram_post(
    post_id: int,
    settings: TelegramPostSettings,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Обновить (перегенерировать) существующий Telegram пост
    """
    # Получаем существующий пост
    telegram_post = session.get(TelegramPost, post_id)
    if not telegram_post:
        raise HTTPException(status_code=404, detail="Telegram пост не найден")

    # Получаем связанную новость
    news_draft = session.get(NewsGenerationDraft, telegram_post.news_draft_id)
    if not news_draft:
        raise HTTPException(status_code=404, detail="Связанная новость не найдена")

    # Получаем оригинальную статью
    from database.models import Article
    article = session.get(Article, news_draft.article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Оригинальная статья не найдена")

    try:
        # Генерируем новый пост
        ai_service = get_ai_service()

        # Формируем URL опубликованной новости
        published_url = None
        if news_draft.bitrix_id:
            # Формируем правильные URL для каждого проекта
            # TODO: В будущем заменить на реальные URL, сохранённые из Bitrix API
            project_urls = {
                "gynecology.school": f"https://gynecology.school/content/articles/news/{news_draft.bitrix_id}/",
                "therapy.school": f"https://therapy.school/content/articles/news/{news_draft.bitrix_id}/",
                "pediatrics.school": f"https://pediatrics.school/content/articles/news/{news_draft.bitrix_id}/"
            }
            published_url = project_urls.get(news_draft.project)

        # Генерируем новый пост
        generated_post = await ai_service.generate_telegram_post(
            article_text=news_draft.generated_news_text or article.content,
            article_title=news_draft.generated_seo_title or article.title,
            article_url=published_url,
            settings=settings
        )

        # Обновляем запись
        telegram_post.hook_type = settings.hook_type
        telegram_post.disclosure_level = settings.disclosure_level
        telegram_post.call_to_action = settings.call_to_action
        telegram_post.include_image = settings.include_image
        telegram_post.post_text = generated_post
        telegram_post.character_count = len(generated_post)

        session.commit()
        session.refresh(telegram_post)

        return telegram_post

    except Exception as e:
        logger.error(f"Ошибка при обновлении Telegram поста: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении поста: {str(e)}")


@router.delete("/{post_id}")
async def delete_telegram_post(
    post_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Удалить Telegram пост
    """
    telegram_post = session.get(TelegramPost, post_id)
    if not telegram_post:
        raise HTTPException(status_code=404, detail="Telegram пост не найден")

    session.delete(telegram_post)
    session.commit()

    return {"message": "Telegram пост успешно удален"}


@router.post("/{post_id}/publish")
async def publish_telegram_post(
    post_id: int,
    request: TelegramPublishRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Опубликовать Telegram пост в канал
    """
    # Получаем пост
    telegram_post = session.get(TelegramPost, post_id)
    if not telegram_post:
        raise HTTPException(status_code=404, detail="Telegram пост не найден")

    try:
        # Получаем связанную новость для изображения
        news_draft = session.get(NewsGenerationDraft, telegram_post.news_draft_id)

        # Подготавливаем текст поста
        post_text = request.post_text

        # Добавляем ссылку на статью, если она указана
        if request.article_url:
            # Встраиваем ссылку в текст кнопки в HTML формате для Telegram
            post_text += f'\n\n<a href="{request.article_url}">{request.link_button_text}</a>'

        # Отправляем в Telegram
        image_url = news_draft.generated_image_url if news_draft and telegram_post.include_image else None
        await send_to_telegram(post_text, image_url)

        # Обновляем статус поста
        telegram_post.is_published = True
        telegram_post.published_at = datetime.utcnow()

        # Обновляем текст поста, если он был изменен
        if request.post_text != telegram_post.post_text:
            telegram_post.post_text = request.post_text
            telegram_post.character_count = len(request.post_text)

        session.commit()
        session.refresh(telegram_post)

        logger.info(f"Telegram пост {post_id} успешно опубликован в канал")

        return {
            "message": "Пост успешно опубликован в Telegram",
            "post_id": post_id,
            "published_at": telegram_post.published_at
        }

    except Exception as e:
        logger.error(f"Ошибка при публикации Telegram поста: {e}")
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при публикации: {str(e)}")