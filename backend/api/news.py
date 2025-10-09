from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from models.schemas import ParseRequest, AdaptedNews, AdaptationRequest
from services.news_parser_manager import news_parser_manager
from core.config import settings
from database.models import SourceType, ArticleRead, SourceStatsRead, ParseSessionRead
from database.service import news_service
from database.schemas import NewsGenerationDraftRead
from services.news_generation_service import NewsGenerationService
from database.connection import get_session, Session
from sqlmodel import select
import logging
import asyncio
from datetime import datetime, timezone

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/sources", response_model=List[str])
async def get_available_sources():
    """Получить список доступных источников новостей"""
    try:
        sources = news_parser_manager.get_available_sources()
        return sources
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources/info")
async def get_sources_info():
    """Получение информации о всех парсерах"""
    try:
        info = news_parser_manager.get_parser_info()
        return info
    except Exception as e:
        logger.error(f"Error getting sources info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sources info")

@router.get("/sources/test", response_model=dict)
async def test_parser():
    """Тестирование парсера новостей"""
    try:
        # Тестируем первый доступный источник
        sources = news_parser_manager.get_available_sources()
        if not sources:
            raise HTTPException(status_code=500, detail="Нет доступных источников")
        
        test_source = sources[0]
        news_list = await news_parser_manager.parse_news_from_source(
            source=test_source,
            max_articles=3,
            fetch_full_content=False
        )
        
        # Извлекаем заголовки для отображения
        sample_titles = [news.title for news in news_list] if news_list else []
        
        return {
            "status": "success",
            "message": f"Парсер работает! Найдено {len(news_list)} новостей из {test_source}",
            "sample_titles": sample_titles,
            "total_found": len(news_list),
            "tested_source": test_source
        }
    except Exception as e:
        logger.error(f"Error testing parser: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка парсера: {str(e)}")

@router.post("/parse", response_model=dict)
async def parse_news(request: ParseRequest):
    """Парсинг новостей из выбранных источников"""
    try:
        logger.info(f"Starting news parsing: sources={request.sources}, max_articles={request.max_articles}, combine_results={request.combine_results}")
        
        if request.combine_results:
            # Получаем объединенный список новостей
            logger.info("Parsing combined results...")
            articles = await news_parser_manager.get_combined_news(
                sources=request.sources,
                max_articles_per_source=request.max_articles,
                date_filter=request.date_filter,
                fetch_full_content=request.fetch_full_content
            )
            logger.info(f"Combined parsing completed: {len(articles)} articles found")
            return {
                "status": "success",
                "total_articles": len(articles),
                "articles": [article.dict() for article in articles]
            }
        else:
            # Получаем новости по источникам отдельно
            if request.sources:
                logger.info(f"Parsing from specific sources: {request.sources}")
                results = await news_parser_manager.parse_news_from_multiple_sources(
                    sources=request.sources,
                    max_articles_per_source=request.max_articles,
                    date_filter=request.date_filter,
                    fetch_full_content=request.fetch_full_content
                )
            else:
                logger.info("Parsing from all available sources")
                results = await news_parser_manager.parse_all_sources(
                    max_articles_per_source=request.max_articles,
                    date_filter=request.date_filter,
                    fetch_full_content=request.fetch_full_content
                )
            
            # Подсчитываем общее количество статей
            total_articles = sum(len(articles) for articles in results.values())
            logger.info(f"Parsing completed: {total_articles} total articles from {len(results)} sources")
            
            return {
                "status": "success",
                "total_articles": total_articles,
                "sources": results
            }
            
    except Exception as e:
        logger.error(f"Error parsing news: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse news: {str(e)}")

@router.post("/parse-to-db", response_model=dict)
async def parse_news_to_database(request: ParseRequest):
    """Парсинг новостей из выбранных источников с сохранением в PostgreSQL"""
    try:
        logger.info(f"Starting news parsing to DB: sources={request.sources}, max_articles={request.max_articles}")
        
        total_saved = 0
        total_duplicates = 0
        total_errors = 0
        results = {}
        
        # Определяем источники для парсинга
        sources_to_parse = request.sources if request.sources else news_parser_manager.get_available_sources()
        
        for source in sources_to_parse:
            try:
                # Создаем сессию парсинга
                session_id = news_service.create_parse_session(
                    source=SourceType(source), 
                    requested_articles=request.max_articles
                )
                
                logger.info(f"Parsing from {source}...")
                
                # Парсим новости
                articles = await news_parser_manager.parse_news_from_source(
                    source=source,
                    max_articles=request.max_articles,
                    date_filter=request.date_filter,
                    fetch_full_content=request.fetch_full_content
                )
                
                # Сохраняем в базу данных
                save_result = news_service.save_articles(articles, SourceType(source))
                
                # Завершаем сессию парсинга
                news_service.complete_parse_session(
                    session_id=session_id,
                    parsed_count=len(articles),
                    saved_count=save_result["saved"],
                    duplicate_count=save_result["duplicates"]
                )
                
                results[source] = {
                    "parsed": len(articles),
                    "saved": save_result["saved"],
                    "duplicates": save_result["duplicates"],
                    "errors": save_result["errors"]
                }
                
                total_saved += save_result["saved"]
                total_duplicates += save_result["duplicates"]
                total_errors += save_result["errors"]
                
                logger.info(f"Source {source}: parsed={len(articles)}, saved={save_result['saved']}, duplicates={save_result['duplicates']}")
                
            except Exception as e:
                logger.error(f"Error parsing {source}: {e}")
                # Завершаем сессию с ошибкой
                try:
                    news_service.complete_parse_session(
                        session_id=session_id,
                        parsed_count=0,
                        saved_count=0,
                        duplicate_count=0,
                        error_message=str(e)
                    )
                except:
                    pass
                
                results[source] = {
                    "parsed": 0,
                    "saved": 0,
                    "duplicates": 0,
                    "errors": 1,
                    "error": str(e)
                }
                total_errors += 1
        
        return {
            "status": "success",
            "summary": {
                "total_saved": total_saved,
                "total_duplicates": total_duplicates,
                "total_errors": total_errors,
                "sources_processed": len(sources_to_parse)
            },
            "sources": results
        }
            
    except Exception as e:
        logger.error(f"Error parsing news to DB: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse news to DB: {str(e)}")

@router.post("/filter-by-platform")
async def filter_news_by_platform(
    platform: str = Query(..., description="Код платформы (medvestnik)"),
    limit: int = Query(10, description="Количество новостей"),
    days_back: int = Query(7, description="Количество дней назад")
):
    """Фильтрация новостей по релевантности для платформы"""
    try:
        if platform not in settings.PLATFORMS:
            raise HTTPException(status_code=400, detail=f"Неизвестная платформа: {platform}")
        
        # Используем medvestnik как основной источник для фильтрации
        all_news = await news_parser_manager.parse_news_from_source(
            source="medvestnik",
            max_articles=limit*2
        )
        
        # TODO: Реализовать фильтрацию по платформе
        filtered_news = all_news[:limit]  # Временно возвращаем первые новости
        
        return {
            "platform": platform,
            "platform_info": settings.PLATFORMS.get(platform, {}),
            "news": [news.dict() for news in filtered_news],
            "total_parsed": len(all_news),
            "total_relevant": len(filtered_news)
        }
    except Exception as e:
        logger.error(f"Error filtering news: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка фильтрации: {str(e)}")

@router.get("/article", response_model=dict)
async def get_full_article(url: str = Query(..., description="URL статьи для получения полного контента")):
    """Получение полного контента статьи по URL"""
    try:
        # Определяем источник по URL
        source = None
        if "medvestnik.ru" in url:
            source = "medvestnik"
        elif "ria.ru" in url:
            source = "ria"
        elif "aig-journal.ru" in url:
            source = "aig"
        elif "remedium.ru" in url:
            source = "remedium"
        
        if not source:
            raise HTTPException(status_code=400, detail="Неподдерживаемый источник")
        
        parser = news_parser_manager.get_parser(source)
        if not parser:
            raise HTTPException(status_code=500, detail="Парсер недоступен")
        
        # Обеспечиваем наличие активной сессии
        await news_parser_manager._ensure_parser_session(parser)
        
        full_content = await parser._fetch_full_article(url)
        
        if not full_content:
            raise HTTPException(status_code=404, detail="Не удалось получить контент статьи")
        
        # Если возвращается объект NewsSource, извлекаем контент
        if hasattr(full_content, 'content'):
            content_text = full_content.content
            content_length = len(content_text) if content_text else 0
        else:
            content_text = str(full_content)
            content_length = len(content_text)
        
        return {
            "status": "success",
            "url": url,
            "content": content_text,
            "content_length": content_length,
            "source": source
        }
    except Exception as e:
        logger.error(f"Error getting article: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статьи: {str(e)}")

@router.post("/adapt", response_model=AdaptedNews)
async def adapt_news_for_platform(request: AdaptationRequest):
    """Адаптация новости для конкретной платформы с помощью AI"""
    # TODO: Реализовать AI адаптацию
    return AdaptedNews(
        original_title=request.news.title,
        adapted_title=f"[{request.platform.upper()}] {request.news.title}",
        original_content=request.news.content,
        adapted_content=f"Адаптировано для {request.platform}: {request.news.content[:500]}...",
        platform=request.platform,
        adaptation_notes="AI адаптация в разработке"
    )

# Новые эндпоинты для работы с базой данных

@router.get("/articles", response_model=List[ArticleRead])
async def get_articles(
    source: Optional[str] = Query(None, description="Фильтр по источнику"),
    limit: int = Query(1000, description="Количество статей"),
    offset: int = Query(0, description="Смещение для пагинации"),
):
    """Получение статей из базы данных"""
    try:
        source_type = None
        if source:
            # Маппинг источников - в API приходит lowercase, а в БД хранится uppercase
            source_mapping = {
                'ria': SourceType.RIA,
                'medvestnik': SourceType.MEDVESTNIK,
                'aig': SourceType.AIG,
                'remedium': SourceType.REMEDIUM,
                'rbc_medical': SourceType.RBC_MEDICAL
            }
            source_type = source_mapping.get(source.lower())
            if not source_type:
                raise HTTPException(status_code=400, detail=f"Unknown source: {source}")
        
        articles = news_service.get_articles(
            source=source_type,
            limit=limit,
            offset=offset
        )
        
        # Преобразуем SourceType в строки для фронтенда
        for article in articles:
            if hasattr(article.source_site, 'value'):
                article.source_site = article.source_site.value
            elif hasattr(article.source_site, 'name'):
                # Если это enum имя (RIA), преобразуем в значение (ria)
                source_name_to_value = {
                    'RIA': 'ria',
                    'MEDVESTNIK': 'medvestnik',
                    'AIG': 'aig',
                    'REMEDIUM': 'remedium',
                    'RBC_MEDICAL': 'rbc_medical'
                }
                article.source_site = source_name_to_value.get(str(article.source_site).split('.')[-1], str(article.source_site))
        
        return articles
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting articles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get articles: {str(e)}")

@router.get("/stats", response_model=List[SourceStatsRead])
async def get_source_statistics():
    """Получение статистики по источникам"""
    try:
        stats = news_service.get_source_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/dashboard")
async def get_dashboard_data():
    """Получение данных для дашборда"""
    try:
        dashboard_data = news_service.get_dashboard_stats()
        return dashboard_data
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")

@router.get("/sessions", response_model=List[ParseSessionRead])
async def get_parse_sessions(
    source: Optional[str] = Query(None, description="Фильтр по источнику"),
    limit: int = Query(20, description="Количество сессий", le=100)
):
    """Получение истории сессий парсинга"""
    try:
        source_type = SourceType(source) if source else None
        sessions = news_service.get_parse_sessions(source=source_type, limit=limit)
        return sessions
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@router.get("/article/{article_id}")
async def get_article_by_id(article_id: int):
    """Получение статьи по ID"""
    try:
        from database.connection import DatabaseSession
        from sqlmodel import select
        from database.models import Article
        
        with DatabaseSession() as session:
            article = session.get(Article, article_id)
            if not article:
                raise HTTPException(status_code=404, detail="Article not found")
            return article
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get article: {str(e)}")

@router.delete("/article/{article_id}")
async def delete_article(article_id: int):
    """Удаление статьи по ID"""
    try:
        from database.connection import DatabaseSession
        from database.models import Article
        
        with DatabaseSession() as session:
            article = session.get(Article, article_id)
            if not article:
                raise HTTPException(status_code=404, detail="Article not found")
            
            session.delete(article)
            return {"message": f"Article {article_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete article: {str(e)}")

@router.post("/parse-with-batch-save", response_model=dict)
async def parse_news_with_batch_save(request: ParseRequest):
    """Парсинг новостей с промежуточным сохранением пакетами по 10 штук"""
    try:
        logger.info(f"Starting batch parsing: sources={request.sources}, max_articles={request.max_articles}")
        
        if not request.sources:
            raise HTTPException(status_code=400, detail="Укажите хотя бы один источник для парсинга")
        
        total_results = {}
        overall_saved = 0
        overall_duplicates = 0
        overall_errors = 0
        
        # Обрабатываем каждый источник по очереди
        for source in request.sources:
            logger.info(f"Processing source: {source}")
            
            try:
                # Получаем парсер
                parser = news_parser_manager.get_parser(source)
                if not parser:
                    logger.error(f"Parser for {source} not found")
                    total_results[source] = {
                        "status": "error",
                        "message": f"Parser for {source} not found",
                        "parsed": 0,
                        "saved": 0,
                        "duplicates": 0,
                        "errors": 1
                    }
                    overall_errors += 1
                    continue
                
                # Обеспечиваем наличие активной сессии
                await news_parser_manager._ensure_parser_session(parser)
                
                # Создаем сессию парсинга
                session_id = news_service.create_parse_session(
                    source=SourceType(source), 
                    requested_articles=request.max_articles
                )
                
                source_saved = 0
                source_duplicates = 0
                source_errors = 0
                
                # Функция для сохранения пакета статей
                async def save_batch(articles_batch):
                    nonlocal source_saved, source_duplicates, source_errors
                    try:
                        save_result = news_service.save_articles(articles_batch, SourceType(source))
                        batch_saved = save_result["saved"]
                        batch_duplicates = save_result["duplicates"] 
                        batch_errors = save_result["errors"]
                        
                        source_saved += batch_saved
                        source_duplicates += batch_duplicates
                        source_errors += batch_errors
                        
                        logger.info(f"[{source}] Batch saved: {batch_saved} new, {batch_duplicates} duplicates, {batch_errors} errors")
                        return batch_saved
                    except Exception as e:
                        logger.error(f"[{source}] Error saving batch: {e}")
                        source_errors += len(articles_batch)
                        return 0
                
                # Запускаем парсинг с промежуточным сохранением
                if hasattr(parser, 'parse_news_list_with_batch_save'):
                    # Используем специальный метод с пакетным сохранением (только для RIA пока)
                    articles = await parser.parse_news_list_with_batch_save(
                        max_articles=request.max_articles,
                        date_filter=request.date_filter,
                        fetch_full_content=request.fetch_full_content,
                        batch_size=10,
                        save_callback=save_batch
                    )
                else:
                    # Для остальных парсеров используем обычный парсинг + сохранение в конце
                    logger.info(f"[{source}] Using standard parsing (no batch save support)")
                    articles = await parser.parse_news_list(
                        max_articles=request.max_articles,
                        date_filter=request.date_filter,
                        fetch_full_content=request.fetch_full_content
                    )
                    
                    # Сохраняем все статьи сразу
                    if articles:
                        save_result = news_service.save_articles(articles, SourceType(source))
                        source_saved = save_result["saved"]
                        source_duplicates = save_result["duplicates"]
                        source_errors = save_result["errors"]
                        logger.info(f"[{source}] Saved all articles: {source_saved} new, {source_duplicates} duplicates, {source_errors} errors")
                
                # Завершаем сессию парсинга
                news_service.complete_parse_session(
                    session_id=session_id,
                    parsed_count=len(articles),
                    saved_count=source_saved,
                    duplicate_count=source_duplicates
                )
                
                # Сохраняем результат для этого источника
                total_results[source] = {
                    "status": "success",
                    "parsed": len(articles),
                    "saved": source_saved,
                    "duplicates": source_duplicates,
                    "errors": source_errors
                }
                
                overall_saved += source_saved
                overall_duplicates += source_duplicates
                overall_errors += source_errors
                
                logger.info(f"[{source}] Completed: parsed={len(articles)}, saved={source_saved}, duplicates={source_duplicates}")
                
            except Exception as e:
                logger.error(f"[{source}] Error during parsing: {e}")
                total_results[source] = {
                    "status": "error",
                    "message": str(e),
                    "parsed": 0,
                    "saved": 0,
                    "duplicates": 0,
                    "errors": 1
                }
                overall_errors += 1
                
                # Завершаем сессию с ошибкой
                try:
                    news_service.complete_parse_session(
                        session_id=session_id,
                        parsed_count=0,
                        saved_count=0,
                        duplicate_count=0,
                        error_message=str(e)
                    )
                except:
                    pass
        
        # Формируем итоговый результат
        result = {
            "status": "success",
            "sources": total_results,
            "total_parsed": sum(r.get("parsed", 0) for r in total_results.values()),
            "total_saved": overall_saved,
            "total_duplicates": overall_duplicates,
            "total_errors": overall_errors,
            "message": f"Парсинг завершен. Обработано источников: {len(request.sources)}. Сохранено {overall_saved} новых статей."
        }
        
        logger.info(f"Multi-source batch parsing completed: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch parsing: {e}")
        raise HTTPException(status_code=500, detail=f"Batch parsing failed: {str(e)}")

@router.delete("/articles/source/{source}")
async def delete_articles_by_source(source: str):
    """Удаление всех статей по источнику"""
    try:
        # Маппинг источников
        source_mapping = {
            'ria': SourceType.RIA,
            'medvestnik': SourceType.MEDVESTNIK,
            'aig': SourceType.AIG,
            'remedium': SourceType.REMEDIUM,
            'rbc_medical': SourceType.RBC_MEDICAL
        }
        
        source_type = source_mapping.get(source.lower())
        if not source_type:
            raise HTTPException(status_code=400, detail=f"Unknown source: {source}")
        
        deleted_count = news_service.delete_articles_by_source(source_type)
        
        return {
            "message": f"Successfully deleted articles from {source}",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error deleting articles from {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles-with-publication-status", response_model=List[dict])
async def get_articles_with_publication_status(
    source: Optional[str] = Query(None, description="Фильтр по источнику"),
    limit: int = Query(1000, description="Количество статей"),
    offset: int = Query(0, description="Смещение для пагинации"),
):
    """Получение статей с информацией о публикации"""
    try:
        source_type = None
        if source:
            # Маппинг источников
            source_mapping = {
                'ria': SourceType.RIA,
                'medvestnik': SourceType.MEDVESTNIK,
                'aig': SourceType.AIG,
                'remedium': SourceType.REMEDIUM,
                'rbc_medical': SourceType.RBC_MEDICAL,
                'url': SourceType.URL
            }
            source_type = source_mapping.get(source.lower())
            if not source_type:
                raise HTTPException(status_code=400, detail=f"Unknown source: {source}")
        
        # Получаем статьи
        articles = news_service.get_articles(
            source=source_type,
            limit=limit,
            offset=offset
        )
        
        # Получаем черновики и публикации для статей
        news_generation_service = NewsGenerationService()

        result = []
        for article in articles:
            # Получаем все черновики для статьи
            drafts = news_generation_service.get_drafts_by_article(article.id)

            # Получаем публикации из черновиков
            publications = []

            # Маппинг кода проекта -> название
            code_to_name = {
                'GS': 'Gynecology School',
                'TS': 'Therapy School',
                'PS': 'Pediatrics School',
                'TEST': 'Test Project',
                'TEST2': 'Test Project 2'
            }

            for draft in drafts:
                if draft.is_published and draft.published_project_code:
                    publications.append({
                        'project_code': draft.published_project_code,
                        'project_name': code_to_name.get(draft.published_project_code, draft.published_project_code),
                        'bitrix_id': draft.bitrix_id,
                        'published_at': draft.published_at.isoformat() if draft.published_at else None
                    })

            unique_pubs = publications
            
            # Находим один опубликованный черновик для обратной совместимости
            published_draft = next((d for d in drafts if d.is_published), None)

            # Находим запланированный черновик по статусу "scheduled"
            scheduled_draft = next((d for d in drafts if d.status == "scheduled"), None)

            # Проверяем наличие черновиков с готовым контентом
            has_draft = any(d for d in drafts if d.generated_news_text or d.summary)

            # Получаем ID последнего черновика для возможности удаления
            latest_draft = drafts[0] if drafts else None

            # Формируем результат
            article_data = {
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "source": article.source_site.value,
                "published_date": article.published_date,
                "published_time": article.published_time,
                "created_at": article.created_at,
                "content": article.content,
                "author": article.author,
                "views_count": article.views_count,
                # Информация о публикации (legacy + расширенная)
                "is_published": bool(unique_pubs) or (published_draft is not None),
                "is_scheduled": scheduled_draft is not None,
                "scheduled_at": scheduled_draft.scheduled_at.isoformat() if scheduled_draft and scheduled_draft.scheduled_at else None,
                "published_project_code": published_draft.published_project_code if published_draft else (unique_pubs[0]["project_code"] if unique_pubs else None),
                "published_project_name": published_draft.published_project_name if published_draft else (unique_pubs[0]["project_name"] if unique_pubs else None),
                "bitrix_id": published_draft.bitrix_id if published_draft else (unique_pubs[0]["bitrix_id"] if unique_pubs else None),
                "draft_published_at": published_draft.published_at if published_draft else (unique_pubs[0]["published_at"] if unique_pubs else None),
                # Новый массив всех публикаций
                "published_projects": unique_pubs,
                # Информация о черновиках
                "has_draft": has_draft,
                "draft_id": latest_draft.id if latest_draft else None,
            }
            result.append(article_data)
        
        return result

    except Exception as e:
        logger.error(f"Error getting articles with publication status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get articles: {str(e)}")


@router.get("/draft/{draft_id}", response_model=dict)
async def get_draft_by_id(
    draft_id: int,
    session: Session = Depends(get_session)
):
    """Получение данных черновика по ID для редактирования"""
    try:
        from database.models import NewsGenerationDraft

        # Получаем черновик
        draft = session.exec(
            select(NewsGenerationDraft)
            .where(NewsGenerationDraft.id == draft_id)
        ).first()

        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        # Формируем ответ с необходимыми данными для редактора
        draft_data = {
            "id": draft.id,
            "article_id": draft.article_id,
            "project": draft.project,
            "summary": draft.summary,
            "facts": draft.facts,
            "generated_news_text": draft.generated_news_text,
            "generated_seo_title": draft.generated_seo_title,
            "generated_seo_description": draft.generated_seo_description,
            "generated_seo_keywords": draft.generated_seo_keywords,
            "generated_image_prompt": draft.generated_image_prompt,
            "generated_image_url": draft.generated_image_url,
            "status": draft.status,
            "scheduled_at": draft.scheduled_at.isoformat() if draft.scheduled_at else None,
            "is_published": getattr(draft, 'is_published', False),
            "created_at": draft.created_at.isoformat() if draft.created_at else None,
            "updated_at": draft.updated_at.isoformat() if draft.updated_at else None,
            "published_project_code": getattr(draft, 'published_project_code', None),
            "published_project_name": getattr(draft, 'published_project_name', None),
            "bitrix_id": getattr(draft, 'bitrix_id', None)
        }

        return draft_data

    except Exception as e:
        logger.error(f"Error getting draft {draft_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get draft: {str(e)}")