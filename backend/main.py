from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
import asyncio
import httpx
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from api import news, admin, news_generation, auth, users, expenses, image_generation, telegram_posts, url_articles
from api import settings as settings_api
from core.config import settings
from core.env_validator import create_backend_validator
from services.news_parser_manager import NewsParserManager, news_parser_manager
from database.connection import init_database
from database.service import news_service
from database.models import SourceType
from middleware.rate_limiter import initialize_rate_limiter, rate_limit_middleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Валидация переменных окружения при старте
print("🚀 Запуск Backend Service...")
env_validator = create_backend_validator()
env_validator.validate_and_exit_on_error()


async def _parse_all_sources_to_db(max_articles: int = 20):
    """Парсит все доступные источники и сохраняет в базу данных."""
    try:
        sources_to_parse = news_parser_manager.get_available_sources()
        logger.info(f"[Scheduler] Starting parse-to-db for sources={sources_to_parse} max_articles={max_articles}")
        for source in sources_to_parse:
            session_id = None
            try:
                session_id = news_service.create_parse_session(
                    source=SourceType(source),
                    requested_articles=max_articles
                )
                articles = await news_parser_manager.parse_news_from_source(
                    source=source,
                    max_articles=max_articles,
                    fetch_full_content=True
                )
                save_result = news_service.save_articles(articles, SourceType(source))
                news_service.complete_parse_session(
                    session_id=session_id,
                    parsed_count=len(articles),
                    saved_count=save_result["saved"],
                    duplicate_count=save_result["duplicates"]
                )
                logger.info(
                    f"[Scheduler] {source}: parsed={len(articles)}, saved={save_result['saved']}, duplicates={save_result['duplicates']}"
                )
            except Exception as e:
                logger.error(f"[Scheduler] Error parsing {source}: {e}")
                if session_id is not None:
                    try:
                        news_service.complete_parse_session(
                            session_id=session_id,
                            parsed_count=0,
                            saved_count=0,
                            duplicate_count=0,
                            error_message=str(e)
                        )
                    except Exception:
                        pass
    except Exception as e:
        logger.error(f"[Scheduler] Unexpected error in parse loop: {e}")


async def _daily_news_parsing_scheduler():
    """Фоновая задача: ежедневно в 02:00 по Москве запускать парсинг всех источников по 20 шт."""
    while True:
        tz_moscow = ZoneInfo("Europe/Moscow")
        now = datetime.now(tz_moscow)
        target = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if now >= target:
            target = target + timedelta(days=1)
        sleep_seconds = max(1, int((target - now).total_seconds()))
        logger.info(f"[Scheduler] Next auto-parse scheduled at {target.isoformat()} MSK (in {sleep_seconds}s)")
        try:
            await asyncio.sleep(sleep_seconds)
        except asyncio.CancelledError:
            logger.info("[Scheduler] Task cancelled")
            break
        try:
            await _parse_all_sources_to_db(max_articles=20)
        except asyncio.CancelledError:
            logger.info("[Scheduler] Task cancelled during parsing")
            break
        except Exception as e:
            logger.error(f"[Scheduler] Scheduled parsing failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Medical News Automation System...")
    try:
        # Инициализируем базу данных
        init_database()
        print("✅ Database initialized successfully")
        
        # Инициализируем настройки по умолчанию
        from services.settings_service import settings_service
        settings_service.initialize_default_settings()
        print("✅ Default settings initialized")
        
        # Инициализируем администратора
        from services.auth_service import auth_service
        auth_service.initialize_admin()
        print("✅ Admin user initialized")
        
        # Инициализируем rate limiting
        initialize_rate_limiter(settings)
        print("✅ Rate limiting initialized")

        # Запускаем планировщик ежедневного парсинга на 02:00 (по времени сервера)
        try:
            app.state.news_parsing_scheduler_task = asyncio.create_task(_daily_news_parsing_scheduler())
            print("✅ Daily news parsing scheduler started (02:00)")
        except Exception as e:
            logger.error(f"❌ Failed to start news parsing scheduler: {e}")
        
        # Планировщик автопубликации отключён - используется внешний cron
        # try:
        #     from services.scheduler import start_publication_scheduler
        #     app.state.publication_scheduler_task = asyncio.create_task(start_publication_scheduler())
        #     print("✅ Publication scheduler started (every minute)")
        # except Exception as e:
        #     logger.error(f"❌ Failed to start publication scheduler: {e}")
        print("ℹ️  Publication scheduler disabled (using external cron)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Medical News Automation System...")
    
    # Останавливаем планировщик парсинга
    try:
        task = getattr(app.state, "news_parsing_scheduler_task", None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    except Exception as e:
        logger.error(f"Error stopping news parsing scheduler: {e}")
    
    # Планировщик публикации отключён (используется внешний cron)
    # try:
    #     task = getattr(app.state, "publication_scheduler_task", None)
    #     if task:
    #         task.cancel()
    #         try:
    #             await task
    #         except asyncio.CancelledError:
    #             pass
    # except Exception as e:
    #     logger.error(f"Error stopping publication scheduler: {e}")
    # Закрываем все парсеры
    try:
        manager = NewsParserManager()
        await manager.close_all_parsers()
    except Exception as e:
        logger.error(f"Error closing parsers: {e}")

app = FastAPI(
    title="Medical News Automation System",
    description="Система автоматизации создания новостных материалов для медицинских платформ",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Timeout middleware для долгих операций
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Middleware для обработки timeout долгих операций"""
    # Увеличиваем timeout для долгих операций
    if request.url.path.startswith("/api/news/parse"):
        timeout = 300  # 5 минут для парсинга
    elif request.url.path.startswith("/api/news-generation/generate-article"):
        timeout = 300  # 5 минут для генерации статей с изображениями
    elif request.url.path.startswith("/api/url-articles/generate-from-url"):
        timeout = 300  # 5 минут для парсинга URL и генерации
    else:
        timeout = 60   # 1 минута для остальных операций
    
    try:
        response = await asyncio.wait_for(call_next(request), timeout=timeout)
        return response
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=408,
            content={"detail": f"Request timeout after {timeout} seconds"}
        )

# Include routers
app.include_router(news.router, prefix="/api/news", tags=["news"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(news_generation.router, tags=["news-generation"])
app.include_router(settings_api.router, prefix="/api", tags=["settings"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["expenses"])
app.include_router(image_generation.router, prefix="/api/images", tags=["image-generation"])
app.include_router(telegram_posts.router, tags=["telegram-posts"])
app.include_router(url_articles.router, prefix="/api/url-articles", tags=["url-articles"])

# Mount static files for generated images
from pathlib import Path
STORAGE_DIR = Path(__file__).parent / "storage" / "images"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(STORAGE_DIR), html=False), name="images")


@app.get("/")
async def root():
    return {"message": "Medical News Automation System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "medical-news-automation"}

@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy", "service": "medical-news-automation"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )