from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime

from models.schemas import PlatformType
from core.config import settings
from services.db_monitoring import db_monitor

router = APIRouter()

@router.get("/platforms")
async def get_platforms():
    """Получение списка доступных платформ"""
    return {
        "platforms": settings.PLATFORMS,
        "available_types": [platform.value for platform in PlatformType]
    }

@router.get("/stats/parsing")
async def get_parsing_stats():
    """Статистика парсинга (заглушка)"""
    return {
        "total_parsed": 0,
        "today_parsed": 0,
        "sources_active": 1,
        "last_parse_time": None,
        "success_rate": 0.0
    }

@router.get("/stats/adaptation")
async def get_adaptation_stats():
    """Статистика адаптации новостей (заглушка)"""
    return {
        "total_adapted": 0,
        "by_platform": {
            "GS": 0,
            "PS": 0, 
            "TS": 0
        },
        "success_rate": 0.0,
        "avg_processing_time": 0.0
    }

@router.get("/config")
async def get_config():
    """Получение конфигурации системы"""
    return {
        "medvestnik_url": settings.MEDVESTNIK_NEWS_URL,
        "platforms": settings.PLATFORMS,
        "api_version": "1.0.0",
        "features": {
            "parsing": True,
            "ai_adaptation": False,  # Пока не реализовано
            "auto_publishing": False,  # Пока не реализовано
            "rate_limiting": settings.RATE_LIMITING_ENABLED
        }
    }

@router.get("/stats/rate-limiting")
async def get_rate_limiting_stats():
    """Статистика rate limiting"""
    from middleware.rate_limiter import rate_limiter
    
    if not rate_limiter or not settings.RATE_LIMITING_ENABLED:
        return {
            "enabled": False,
            "message": "Rate limiting is disabled"
        }
    
    try:
        stats = rate_limiter.get_stats()
        return {
            "enabled": True,
            "stats": stats,
            "config": {
                "auth_limit": settings.RATE_LIMIT_AUTH,
                "parsing_limit": settings.RATE_LIMIT_PARSING,
                "generation_limit": settings.RATE_LIMIT_GENERATION,
                "admin_limit": settings.RATE_LIMIT_ADMIN,
                "default_limit": settings.RATE_LIMIT_DEFAULT
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting rate limiting stats: {str(e)}")

@router.get("/stats/database")
async def get_database_stats():
    """Статистика производительности базы данных"""
    try:
        # Собираем актуальные метрики
        metrics = db_monitor.collect_metrics()
        
        # Проверяем условия для алертов
        alerts = db_monitor.get_alert_conditions(metrics)
        
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "connections": {
                "active": metrics.active_connections,
                "total": metrics.total_connections,
                "max": metrics.max_connections,
                "usage_percent": round((metrics.active_connections / metrics.max_connections) * 100, 1) if metrics.max_connections > 0 else 0
            },
            "performance": {
                "queries_per_second": round(metrics.queries_per_second, 2),
                "avg_query_time": round(metrics.avg_query_time, 2),
                "slow_queries_count": metrics.slow_queries_count
            },
            "resources": {
                "database_size": metrics.database_size,
                "database_size_formatted": db_monitor.format_size(metrics.database_size),
                "cache_hit_ratio": metrics.cache_hit_ratio,
                "index_hit_ratio": metrics.index_hit_ratio
            },
            "locks": {
                "total_locks": metrics.locks_count,
                "waiting_queries": metrics.waiting_queries
            },
            "alerts": alerts,
            "health_status": "critical" if len(alerts) > 3 else "warning" if len(alerts) > 0 else "healthy"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error collecting database stats: {str(e)}")

@router.get("/stats/database/tables")
async def get_database_table_stats():
    """Детальная статистика по таблицам базы данных"""
    try:
        metrics = db_monitor.collect_metrics()
        
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "tables": metrics.table_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error collecting table stats: {str(e)}")

@router.get("/stats/database/history")
async def get_database_history(hours: int = 1):
    """История метрик базы данных за указанное количество часов"""
    try:
        if hours < 1 or hours > 24:
            raise HTTPException(status_code=400, detail="Hours must be between 1 and 24")
        
        history = db_monitor.get_metrics_history(hours=hours)
        
        return {
            "period_hours": hours,
            "metrics_count": len(history),
            "metrics": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "active_connections": m.active_connections,
                    "queries_per_second": round(m.queries_per_second, 2),
                    "avg_query_time": round(m.avg_query_time, 2),
                    "cache_hit_ratio": m.cache_hit_ratio,
                    "slow_queries": m.slow_queries_count,
                    "waiting_queries": m.waiting_queries
                }
                for m in history
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database history: {str(e)}")

@router.post("/database/analyze")
async def run_database_analyze():
    """Запустить ANALYZE для всех таблиц (обновление статистики планировщика)"""
    try:
        from database.connection import engine
        from sqlmodel import Session, text
        
        with Session(engine) as session:
            # Запускаем ANALYZE для всех пользовательских таблиц
            session.exec(text("ANALYZE"))
            session.commit()
        
        return {
            "success": True,
            "message": "Database ANALYZE completed successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running database analyze: {str(e)}")

@router.post("/database/vacuum")
async def run_database_vacuum():
    """Запустить VACUUM для очистки мертвых кортежей"""
    try:
        from database.connection import engine
        from sqlmodel import Session, text
        
        with Session(engine) as session:
            # Запускаем VACUUM (неблокирующий)
            session.exec(text("VACUUM"))
            session.commit()
        
        return {
            "success": True,
            "message": "Database VACUUM completed successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running database vacuum: {str(e)}")