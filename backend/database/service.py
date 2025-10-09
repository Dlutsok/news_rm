"""
Сервис для работы с базой данных новостей
"""

from datetime import datetime, timedelta
from database.models import moscow_now
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func, and_, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
import logging

from database.models import Article, SourceStats, ParseSession, SourceType
from database.connection import DatabaseSession, get_db_session
from models.schemas import NewsSource

logger = logging.getLogger(__name__)


class NewsService:
    """Сервис для работы с новостями в базе данных"""
    
    def __init__(self):
        self.session = None
    
    def save_articles(self, articles: List[NewsSource], source: SourceType) -> Dict[str, int]:
        """
        Сохранение списка статей в базу данных
        
        Args:
            articles: Список статей для сохранения
            source: Источник новостей
            
        Returns:
            Словарь с количеством сохраненных и дублированных статей
        """
        saved_count = 0
        duplicate_count = 0
        error_count = 0
        
        with DatabaseSession() as session:
            for article_data in articles:
                try:
                    # Конвертируем HttpUrl в строку для SQL запросов
                    url_str = str(article_data.url)

                    # Проверяем существование статьи по URL
                    existing = session.exec(
                        select(Article).where(Article.url == url_str)
                    ).first()

                    if existing:
                        duplicate_count += 1
                        logger.debug(f"Duplicate article found: {url_str}")
                        continue

                    # Создаем новую статью
                    article = Article(
                        title=article_data.title,
                        url=url_str,
                        content=article_data.content,
                        source_site=source,
                        published_date=article_data.published_date,
                        published_time=article_data.published_time,
                        views_count=article_data.views_count,
                        author=article_data.author,
                        created_at=moscow_now()
                    )
                    
                    session.add(article)
                    saved_count += 1
                    logger.info(f"Saved article: {article_data.title[:50]}...")
                    
                except IntegrityError as e:
                    duplicate_count += 1
                    logger.warning(f"Integrity error (duplicate): {e}")
                    session.rollback()
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error saving article {str(article_data.url)}: {e}")
                    session.rollback()
        
        # Обновляем статистику источника
        self.update_source_stats(source, saved_count)
        
        return {
            "saved": saved_count,
            "duplicates": duplicate_count,
            "errors": error_count,
            "total_processed": len(articles)
        }
    
    def get_articles(
        self, 
        source: Optional[SourceType] = None,
        limit: int = 50,
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Article]:
        """Получение статей с фильтрацией"""
        
        with DatabaseSession() as session:
            query = select(Article)
            
            # Фильтр по источнику
            if source:
                # В БД хранится как SourceType.RIA, поэтому сравниваем с enum напрямую
                query = query.where(Article.source_site == source)
            
            # Фильтр по дате
            if date_from:
                query = query.where(Article.created_at >= date_from)
            if date_to:
                query = query.where(Article.created_at <= date_to)
            
            # Сортировка и пагинация - сначала по дате публикации, потом по дате создания
            query = query.order_by(
                Article.published_date.desc().nulls_last(),
                Article.created_at.desc()
            )
            query = query.offset(offset).limit(limit)
            
            articles = session.exec(query).all()
            
            # Принудительно загружаем все атрибуты внутри сессии
            loaded_articles = []
            for article in articles:
                # Создаем новый объект с загруженными данными
                loaded_article = Article(
                    id=article.id,
                    title=article.title,
                    url=article.url,
                    content=article.content,
                    source_site=article.source_site,
                    published_date=article.published_date,
                    published_time=article.published_time,
                    views_count=article.views_count,
                    author=article.author,
                    created_at=article.created_at,
                    updated_at=article.updated_at,
                    is_processed=article.is_processed,
                    processing_status=article.processing_status
                )
                loaded_articles.append(loaded_article)
            
            return loaded_articles
    
    def get_article_by_url(self, url: str) -> Optional[Article]:
        """Получение статьи по URL"""
        with DatabaseSession() as session:
            return session.exec(
                select(Article).where(Article.url == url)
            ).first()
    
    def get_source_stats(self, source: Optional[SourceType] = None) -> List[SourceStats]:
        """Получение статистики по источникам"""
        with DatabaseSession() as session:
            query = select(SourceStats)
            
            if source:
                query = query.where(SourceStats.source_site == source)
            
            stats = session.exec(query).all()
            
            # Создаем отсоединенные объекты
            loaded_stats = []
            for stat in stats:
                loaded_stat = SourceStats(
                    id=stat.id,
                    source_site=stat.source_site,
                    total_articles=stat.total_articles,
                    last_update=stat.last_update,
                    last_successful_parse=stat.last_successful_parse,
                    parse_errors_count=stat.parse_errors_count
                )
                loaded_stats.append(loaded_stat)
            
            return loaded_stats
    
    def update_source_stats(self, source: SourceType, new_articles_count: int = 0):
        """Обновление статистики источника"""
        with DatabaseSession() as session:
            # Получаем или создаем статистику
            stats = session.exec(
                select(SourceStats).where(SourceStats.source_site == source)
            ).first()
            
            if not stats:
                stats = SourceStats(source_site=source)
                session.add(stats)
            
            # Обновляем счетчики
            # Приводим к naive datetime, так как БД хранит без tzinfo
            now = moscow_now()
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            today = now.date()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            # Общее количество статей
            total_count = session.exec(
                select(func.count(Article.id)).where(Article.source_site == source)
            ).first() or 0
            
            # Статьи за сегодня
            today_count = session.exec(
                select(func.count(Article.id)).where(
                    and_(
                        Article.source_site == source,
                        func.date(Article.created_at) == today
                    )
                )
            ).first() or 0
            
            # Статьи за неделю
            week_count = session.exec(
                select(func.count(Article.id)).where(
                    and_(
                        Article.source_site == source,
                        Article.created_at >= week_ago
                    )
                )
            ).first() or 0
            
            # Статьи за месяц
            month_count = session.exec(
                select(func.count(Article.id)).where(
                    and_(
                        Article.source_site == source,
                        Article.created_at >= month_ago
                    )
                )
            ).first() or 0
            
            # Последняя статья
            last_article = session.exec(
                select(Article).where(Article.source_site == source)
                .order_by(Article.created_at.desc())
                .limit(1)
            ).first()
            
            # Обновляем статистику
            stats.total_articles = total_count
            stats.articles_today = today_count
            stats.articles_this_week = week_count
            stats.articles_this_month = month_count
            stats.last_parsed_at = now
            stats.updated_at = now
            
            if last_article:
                stats.last_article_date = last_article.created_at
            
            session.add(stats)
            logger.info(f"Updated stats for {source}: total={total_count}, today={today_count}")
    
    def create_parse_session(self, source: SourceType, requested_articles: int) -> int:
        """Создание сессии парсинга"""
        with DatabaseSession() as session:
            parse_session = ParseSession(
                source_site=source,
                requested_articles=requested_articles,
                status="started",
                started_at=moscow_now()
            )
            session.add(parse_session)
            session.commit()
            session.refresh(parse_session)
            return parse_session.id
    
    def complete_parse_session(
        self, 
        session_id: int, 
        parsed_count: int, 
        saved_count: int, 
        duplicate_count: int,
        error_message: Optional[str] = None
    ):
        """Завершение сессии парсинга"""
        with DatabaseSession() as session:
            parse_session = session.get(ParseSession, session_id)
            if parse_session:
                # Приводим обе даты к naive, чтобы избежать ошибки смешивания aware/naive
                now = moscow_now()
                started = parse_session.started_at
                if now.tzinfo is not None:
                    now = now.replace(tzinfo=None)
                if started and started.tzinfo is not None:
                    started = started.replace(tzinfo=None)
                duration = (now - started).total_seconds()
                
                parse_session.parsed_articles = parsed_count
                parse_session.saved_articles = saved_count
                parse_session.duplicate_articles = duplicate_count
                parse_session.completed_at = now
                parse_session.duration_seconds = int(duration)
                parse_session.status = "failed" if error_message else "completed"
                parse_session.error_message = error_message
                
                session.add(parse_session)
                logger.info(f"Parse session {session_id} completed in {duration:.1f}s")
    
    def get_parse_sessions(self, source: Optional[SourceType] = None, limit: int = 20) -> List[ParseSession]:
        """Получение истории сессий парсинга"""
        with DatabaseSession() as session:
            query = select(ParseSession)
            
            if source:
                query = query.where(ParseSession.source_site == source)
            
            query = query.order_by(ParseSession.started_at.desc()).limit(limit)
            return session.exec(query).all()
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Получение статистики для дашборда"""
        with DatabaseSession() as session:
            # Общая статистика
            total_articles = session.exec(select(func.count(Article.id))).first() or 0
            
            # Статистика по источникам
            source_stats = session.exec(
                select(Article.source_site, func.count(Article.id))
                .group_by(Article.source_site)
            ).all()
            
            # Статистика за последние дни
            now = moscow_now()
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            daily_stats = []
            
            for i in range(7):  # Последние 7 дней
                date = (now - timedelta(days=i)).date()
                count = session.exec(
                    select(func.count(Article.id))
                    .where(func.date(Article.created_at) == date)
                ).first() or 0
                
                daily_stats.append({
                    "date": date.isoformat(),
                    "count": count
                })
            
            # Последние сессии парсинга
            recent_sessions = session.exec(
                select(ParseSession)
                .order_by(ParseSession.started_at.desc())
                .limit(10)
            ).all()
            
            return {
                "total_articles": total_articles,
                "sources": dict(source_stats),
                "daily_stats": daily_stats,
                "recent_sessions": [
                    {
                        "id": s.id,
                        "source": s.source_site,
                        "status": s.status,
                        "saved": s.saved_articles,
                        "started_at": s.started_at.isoformat() if s.started_at else None
                    }
                    for s in recent_sessions
                ]
            }
    
    def delete_articles_by_source(self, source: SourceType) -> int:
        """Удаление всех статей по источнику"""
        with DatabaseSession() as session:
            # Подсчитываем количество статей для удаления
            count_query = select(func.count(Article.id)).where(Article.source_site == source)
            count = session.exec(count_query).first() or 0
            
            # Удаляем статьи
            delete_query = select(Article).where(Article.source_site == source)
            articles_to_delete = session.exec(delete_query).all()
            
            for article in articles_to_delete:
                session.delete(article)
            
            session.commit()
            logger.info(f"Deleted {count} articles from source {source}")
            return count


# Глобальный экземпляр сервиса
news_service = NewsService()