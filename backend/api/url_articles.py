"""
API endpoints для генерации статей из внешних URL
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session
from typing import Optional
import logging

from database.models import (
    NewsGenerationDraft, User, ProjectType,
    GenerationLog, Article, SourceType, NewsStatus
)
from database.schemas import (
    URLArticleParseRequest, URLArticleParseResponse,
    URLArticleGenerationRequest, URLArticleGenerationResponse
)
from database.connection import get_session
from api.dependencies import require_staff
from services.url_article_parser import url_parser
from services.ai_service import get_ai_service
import json

logger = logging.getLogger(__name__)

router = APIRouter(tags=["URL Articles"])


@router.post("/parse", response_model=URLArticleParseResponse)
async def parse_url_article(
    request: URLArticleParseRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_staff)
):
    """
    Парсинг статьи из URL (без генерации)
    Использует Jina AI Reader для извлечения контента и сохраняет в БД
    """
    try:
        logger.info(f"User {current_user.username} parsing URL: {request.url}")

        # Шаг 1: Парсим URL через Jina AI + trafilatura fallback
        async with url_parser:
            parse_result = await url_parser.parse_article(request.url)

        if not parse_result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=parse_result['error'] or "Не удалось распарсить URL"
            )

        # Шаг 2: Дополнительная очистка через GPT-4o mini
        ai_service = get_ai_service()
        cleaned_content, cleaning_metrics = await ai_service.clean_article_content(
            parse_result['content'],
            request.url
        )

        logger.info(f"Article cleaned: {cleaning_metrics.get('reduction_percent', 0)}% reduction, "
                   f"{cleaning_metrics.get('tokens_used', 0)} tokens used")

        # Используем очищенный контент
        parse_result['content'] = cleaned_content

        # Извлекаем заголовок из контента (первый заголовок H1)
        content = parse_result['content']
        title = parse_result['domain']  # По умолчанию используем домен

        # Пытаемся найти заголовок в markdown
        import re
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title_match = re.search(r'^Title:\s*(.+)$', content, re.MULTILINE)

        if h1_match:
            title = h1_match.group(1).strip()
        elif title_match:
            title = title_match.group(1).strip()
        else:
            # Берем первую строку с текстом
            first_line = next((line.strip() for line in content.split('\n') if line.strip() and len(line.strip()) > 10), None)
            if first_line:
                title = first_line[:200]  # Ограничиваем длину заголовка

        # Проверяем, не существует ли уже статья с таким URL
        existing_article = session.query(Article).filter(Article.url == parse_result['url']).first()

        if existing_article:
            logger.info(f"Article already exists: {existing_article.id}")
            article_id = existing_article.id
        else:
            # Создаем новую статью в БД
            article = Article(
                title=title,
                url=parse_result['url'],
                content=content,
                source_site=SourceType.URL,
                published_date=None,
                author=parse_result['domain'],
                is_processed=False
            )

            session.add(article)
            session.commit()
            session.refresh(article)

            article_id = article.id
            logger.info(f"Created new article from URL: id={article_id}, title={title[:50]}")

        return URLArticleParseResponse(
            success=True,
            url=parse_result['url'],
            content=parse_result['content'],
            domain=parse_result['domain'],
            article_id=article_id,
            title=title,
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error parsing URL {request.url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при парсинге URL: {str(e)}"
        )


@router.post("/generate-from-url", response_model=URLArticleGenerationResponse)
async def generate_article_from_url(
    request: URLArticleGenerationRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_staff)
):
    """
    Полный цикл: парсинг URL + генерация адаптированной медицинской статьи

    1. Парсит контент через Jina AI Reader
    2. Генерирует профессиональную медицинскую статью через GPT
    3. Создает изображение через YandexART (опционально)
    4. Сохраняет как черновик в БД
    """
    try:
        logger.info(f"User {current_user.username} generating article from URL: {request.url}")

        # Шаг 1: Парсим URL
        async with url_parser:
            parse_result = await url_parser.parse_article(request.url)

        if not parse_result['success']:
            return URLArticleGenerationResponse(
                success=False,
                draft_id=None,
                source_url=request.url,
                source_domain=parse_result.get('domain', ''),
                news_text=None,
                seo_title=None,
                seo_description=None,
                seo_keywords=None,
                image_url=None,
                error=parse_result.get('error', 'Не удалось распарсить URL')
            )

        source_url = parse_result['url']
        source_domain = parse_result['domain']
        raw_content = parse_result['content']

        logger.info(f"Successfully parsed {source_url}, raw content length: {len(raw_content)} chars")

        # Шаг 1.5: Очистка через GPT-4o mini
        ai_service = get_ai_service()
        cleaned_content, cleaning_metrics = await ai_service.clean_article_content(
            raw_content,
            source_url
        )

        logger.info(f"Article cleaned: {cleaning_metrics.get('reduction_percent', 0)}% reduction, "
                   f"{cleaning_metrics.get('tokens_used', 0)} tokens, "
                   f"from {len(raw_content)} to {len(cleaned_content)} chars")

        external_content = cleaned_content

        # Шаг 2: Генерируем статью через AI (ai_service уже получен выше)

        try:
            article, metrics = await ai_service.generate_article_from_external_content(
                external_content=external_content,
                source_url=source_url,
                source_domain=source_domain,
                project=request.project,
                formatting_options=request.formatting_options
            )

            logger.info(f"Article generated successfully from {source_url}, tokens: {metrics.get('tokens_used', 0)}")

        except Exception as gen_error:
            logger.error(f"AI generation error for {source_url}: {gen_error}")

            # Логируем ошибку генерации
            error_log = GenerationLog(
                draft_id=0,  # Нет draft_id пока
                operation_type="url_article_generation",
                model_used="gpt-4o",
                success=False,
                error_message=str(gen_error),
                tokens_used=0,
                processing_time_seconds=0
            )
            session.add(error_log)
            session.commit()

            return URLArticleGenerationResponse(
                success=False,
                draft_id=None,
                source_url=source_url,
                source_domain=source_domain,
                news_text=None,
                seo_title=None,
                seo_description=None,
                seo_keywords=None,
                image_url=None,
                error=f"Ошибка AI генерации: {str(gen_error)}"
            )

        # Шаг 3: Сохраняем черновик в БД
        draft = NewsGenerationDraft(
            article_id=0,  # URL статьи не имеют article_id из WordPress
            project=request.project.value,
            user_id=current_user.id,
            summary=f"Статья адаптирована из {source_domain}",
            facts=json.dumps([f"Источник: {source_url}"]),
            generated_news_text=article.news_text,
            generated_seo_title=article.seo_title,
            generated_seo_description=article.seo_description,
            generated_seo_keywords=json.dumps(article.seo_keywords),
            generated_image_prompt=article.image_prompt,
            generated_image_url=article.image_url if request.generate_image else None,
            status=NewsStatus.GENERATED
        )

        session.add(draft)
        session.commit()
        session.refresh(draft)

        logger.info(f"Draft created: id={draft.id} from URL {source_url}")

        # Шаг 4: Логируем успешную генерацию
        gen_log = GenerationLog(
            draft_id=draft.id,
            operation_type="url_article_generation",
            model_used=metrics.get('model_used', 'gpt-4o'),
            success=True,
            error_message=None,
            tokens_used=metrics.get('tokens_used', 0),
            processing_time_seconds=metrics.get('processing_time_seconds', 0)
        )
        session.add(gen_log)
        session.commit()

        return URLArticleGenerationResponse(
            success=True,
            draft_id=draft.id,
            source_url=source_url,
            source_domain=source_domain,
            news_text=article.news_text,
            seo_title=article.seo_title,
            seo_description=article.seo_description,
            seo_keywords=article.seo_keywords,
            image_url=article.image_url if request.generate_image else None,
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error in generate_article_from_url: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации статьи из URL: {str(e)}"
        )
