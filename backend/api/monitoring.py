"""
API роутер для системного мониторинга
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.system_monitoring import system_monitor
from services.db_monitoring import db_monitor

router = APIRouter()


@router.get("/system")
async def get_system_metrics():
    """Получить системные метрики (CPU, RAM, Disk)"""
    try:
        metrics = system_monitor.get_system_metrics()
        
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "cpu": {
                "percent": round(metrics.cpu_percent, 1),
                "status": "critical" if metrics.cpu_percent >= 90 else "warning" if metrics.cpu_percent >= 75 else "healthy"
            },
            "memory": {
                "total": metrics.memory_total,
                "used": metrics.memory_used,
                "percent": round(metrics.memory_percent, 1),
                "total_formatted": system_monitor.format_bytes(metrics.memory_total),
                "used_formatted": system_monitor.format_bytes(metrics.memory_used),
                "status": "critical" if metrics.memory_percent >= 90 else "warning" if metrics.memory_percent >= 80 else "healthy"
            },
            "disk": {
                "total": metrics.disk_total,
                "used": metrics.disk_used,
                "percent": round(metrics.disk_percent, 1),
                "total_formatted": system_monitor.format_bytes(metrics.disk_total),
                "used_formatted": system_monitor.format_bytes(metrics.disk_used),
                "status": "critical" if metrics.disk_percent >= 95 else "warning" if metrics.disk_percent >= 85 else "healthy"
            },
            "network": {
                "sent": metrics.network_sent,
                "recv": metrics.network_recv,
                "sent_formatted": system_monitor.format_bytes(metrics.network_sent),
                "recv_formatted": system_monitor.format_bytes(metrics.network_recv)
            },
            "uptime": {
                "seconds": round(metrics.uptime, 0),
                "formatted": system_monitor.format_uptime(metrics.uptime)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error collecting system metrics: {str(e)}")


@router.get("/services")
async def get_services_status():
    """Получить статус всех сервисов"""
    try:
        statuses = await system_monitor.check_all_services()
        
        services_data = {}
        overall_status = "healthy"
        
        for name, status in statuses.items():
            services_data[name] = {
                "name": status.name,
                "url": status.url,
                "status": status.status,
                "response_time": round(status.response_time, 1),
                "last_check": status.last_check.isoformat(),
                "error_message": status.error_message
            }
            
            # Определяем общий статус
            if status.status == "critical":
                overall_status = "critical"
            elif status.status == "warning" and overall_status != "critical":
                overall_status = "warning"
        
        # Подсчитываем статистику
        total_services = len(services_data)
        healthy_services = sum(1 for s in services_data.values() if s["status"] == "healthy")
        warning_services = sum(1 for s in services_data.values() if s["status"] == "warning")
        critical_services = sum(1 for s in services_data.values() if s["status"] == "critical")
        
        return {
            "overall_status": overall_status,
            "statistics": {
                "total": total_services,
                "healthy": healthy_services,
                "warning": warning_services,
                "critical": critical_services
            },
            "services": services_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking services status: {str(e)}")


@router.get("/alerts")
async def get_alerts(
    active_only: bool = Query(False, description="Показать только активные алерты"),
    limit: int = Query(20, ge=1, le=100, description="Максимальное количество алертов")
):
    """Получить алерты"""
    try:
        if active_only:
            alerts = system_monitor.get_active_alerts()
        else:
            alerts = system_monitor.get_all_alerts(limit=limit)
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                "id": alert.id,
                "type": alert.type,
                "title": alert.title,
                "message": alert.message,
                "service": alert.service,
                "timestamp": alert.timestamp.isoformat(),
                "acknowledged": alert.acknowledged
            })
        
        # Подсчитываем статистику по типам
        statistics = {
            "total": len(alerts_data),
            "critical": sum(1 for a in alerts_data if a["type"] == "critical"),
            "warning": sum(1 for a in alerts_data if a["type"] == "warning"),
            "info": sum(1 for a in alerts_data if a["type"] == "info"),
            "active": sum(1 for a in alerts_data if not a["acknowledged"])
        }
        
        return {
            "statistics": statistics,
            "alerts": alerts_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Подтвердить алерт"""
    try:
        success = system_monitor.acknowledge_alert(alert_id)
        
        if success:
            return {
                "success": True,
                "message": f"Alert {alert_id} acknowledged",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error acknowledging alert: {str(e)}")


@router.post("/alerts/clear-all")
async def clear_all_alerts():
    """Очистить все алерты (подтвердить все активные)"""
    try:
        active_alerts = system_monitor.get_active_alerts()
        cleared_count = 0
        
        for alert in active_alerts:
            if system_monitor.acknowledge_alert(alert.id):
                cleared_count += 1
        
        return {
            "success": True,
            "message": f"Cleared {cleared_count} alerts",
            "cleared_count": cleared_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing alerts: {str(e)}")


@router.delete("/alerts/history")
async def clear_alerts_history():
    """Полностью очистить историю алертов"""
    try:
        system_monitor.alerts.clear()
        
        return {
            "success": True,
            "message": "All alerts history cleared",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing alerts history: {str(e)}")


@router.get("/overview")
async def get_monitoring_overview():
    """Получить общий обзор состояния системы"""
    try:
        # Получаем данные от разных мониторов
        system_metrics = system_monitor.get_system_metrics()
        services_status = await system_monitor.check_all_services()
        db_metrics = db_monitor.collect_metrics()
        active_alerts = system_monitor.get_active_alerts()
        
        # Определяем общий статус системы
        overall_status = "healthy"
        
        # Проверяем системные метрики
        if (system_metrics.cpu_percent >= 90 or 
            system_metrics.memory_percent >= 90 or 
            system_metrics.disk_percent >= 95):
            overall_status = "critical"
        elif (system_metrics.cpu_percent >= 75 or 
              system_metrics.memory_percent >= 80 or 
              system_metrics.disk_percent >= 85):
            overall_status = "warning"
        
        # Проверяем сервисы
        for status in services_status.values():
            if status.status == "critical":
                overall_status = "critical"
                break
            elif status.status == "warning" and overall_status != "critical":
                overall_status = "warning"
        
        # Проверяем БД
        db_alerts = db_monitor.get_alert_conditions(db_metrics)
        if len(db_alerts) > 3:
            overall_status = "critical"
        elif len(db_alerts) > 0 and overall_status != "critical":
            overall_status = "warning"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "system": {
                    "cpu_percent": round(system_metrics.cpu_percent, 1),
                    "memory_percent": round(system_metrics.memory_percent, 1),
                    "disk_percent": round(system_metrics.disk_percent, 1),
                    "uptime_formatted": system_monitor.format_uptime(system_metrics.uptime)
                },
                "services": {
                    "total": len(services_status),
                    "healthy": sum(1 for s in services_status.values() if s.status == "healthy"),
                    "warning": sum(1 for s in services_status.values() if s.status == "warning"),
                    "critical": sum(1 for s in services_status.values() if s.status == "critical")
                },
                "database": {
                    "active_connections": db_metrics.active_connections,
                    "cache_hit_ratio": db_metrics.cache_hit_ratio,
                    "size_formatted": db_monitor.format_size(db_metrics.database_size),
                    "alerts_count": len(db_alerts)
                },
                "alerts": {
                    "total": len(active_alerts),
                    "critical": sum(1 for a in active_alerts if a.type == "critical"),
                    "warning": sum(1 for a in active_alerts if a.type == "warning")
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting monitoring overview: {str(e)}")


@router.get("/history")
async def get_metrics_history(
    hours: int = Query(1, ge=1, le=24, description="Количество часов для истории"),
    metric_type: str = Query("system", description="Тип метрик: system или database")
):
    """Получить историю метрик"""
    try:
        if metric_type == "system":
            history = system_monitor.get_metrics_history(hours=hours)
            
            return {
                "type": "system",
                "period_hours": hours,
                "metrics_count": len(history),
                "metrics": [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "cpu_percent": round(m.cpu_percent, 1),
                        "memory_percent": round(m.memory_percent, 1),
                        "disk_percent": round(m.disk_percent, 1),
                        "network_sent": m.network_sent,
                        "network_recv": m.network_recv
                    }
                    for m in history
                ]
            }
        
        elif metric_type == "database":
            history = db_monitor.get_metrics_history(hours=hours)
            
            return {
                "type": "database",
                "period_hours": hours,
                "metrics_count": len(history),
                "metrics": [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "active_connections": m.active_connections,
                        "queries_per_second": round(m.queries_per_second, 2),
                        "avg_query_time": round(m.avg_query_time, 2),
                        "cache_hit_ratio": m.cache_hit_ratio,
                        "slow_queries": m.slow_queries_count
                    }
                    for m in history
                ]
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid metric_type. Use 'system' or 'database'")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics history: {str(e)}")


@router.get("/logs")
async def get_system_logs(
    level: Optional[str] = Query(None, description="Уровень логов: DEBUG, INFO, WARNING, ERROR, CRITICAL"),
    service: Optional[str] = Query(None, description="Фильтр по сервису"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    search: Optional[str] = Query(None, description="Поиск по тексту")
):
    """Получить системные логи (заглушка для будущей реализации)"""
    # Пока что возвращаем mock данные
    # В будущем здесь будет реальное чтение логов из файлов или централизованного хранилища
    
    mock_logs = [
        {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "service": "backend",
            "message": "API server started successfully",
            "module": "main"
        },
        {
            "timestamp": datetime.now().isoformat(),
            "level": "WARNING",
            "service": "database",
            "message": "Slow query detected: 1.5s",
            "module": "sqlalchemy"
        }
    ]
    
    return {
        "logs": mock_logs[:limit],
        "total": len(mock_logs),
        "filters": {
            "level": level,
            "service": service,
            "search": search
        },
        "timestamp": datetime.now().isoformat()
    }