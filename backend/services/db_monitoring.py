"""
Модуль для мониторинга производительности PostgreSQL базы данных
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlmodel import Session, text
from database.connection import engine

logger = logging.getLogger(__name__)


@dataclass
class DBMetrics:
    """Метрики производительности БД"""
    # Основные метрики
    active_connections: int
    total_connections: int
    max_connections: int
    
    # Производительность
    queries_per_second: float
    avg_query_time: float
    slow_queries_count: int
    
    # Использование ресурсов
    database_size: int  # в байтах
    cache_hit_ratio: float
    index_hit_ratio: float
    
    # Блокировки и ожидания
    locks_count: int
    waiting_queries: int
    
    # Статистика таблиц
    table_stats: List[Dict[str, Any]]
    
    # Время сбора метрик
    timestamp: datetime


class DatabaseMonitor:
    """Класс для мониторинга производительности PostgreSQL"""
    
    def __init__(self):
        self.metrics_history: List[DBMetrics] = []
        self.max_history_size = 100  # Храним последние 100 замеров
    
    def collect_metrics(self) -> DBMetrics:
        """Собрать все метрики БД"""
        try:
            with Session(engine) as session:
                # Инициализируем значения по умолчанию
                connections = {'active': 0, 'total': 0, 'max': 0}
                performance = {'qps': 0.0, 'avg_time': 0.0, 'slow_queries': 0}
                resources = {'db_size': 0, 'cache_hit_ratio': 0.0, 'index_hit_ratio': 0.0}
                locks = {'total_locks': 0, 'waiting': 0}
                table_stats = []
                
                try:
                    # Метрики соединений
                    connections = self._get_connection_stats(session)
                except Exception as e:
                    logger.warning(f"Error getting connection stats: {e}")
                    try:
                        session.rollback()
                    except Exception:
                        pass
                
                try:
                    # Метрики производительности
                    performance = self._get_performance_stats(session)
                except Exception as e:
                    logger.warning(f"Error getting performance stats: {e}")
                    try:
                        session.rollback()
                    except Exception:
                        pass
                
                try:
                    # Использование ресурсов
                    resources = self._get_resource_stats(session)
                except Exception as e:
                    logger.warning(f"Error getting resource stats: {e}")
                    try:
                        session.rollback()
                    except Exception:
                        pass
                
                try:
                    # Блокировки
                    locks = self._get_lock_stats(session)
                except Exception as e:
                    logger.warning(f"Error getting lock stats: {e}")
                    try:
                        session.rollback()
                    except Exception:
                        pass
                
                try:
                    # Статистика таблиц
                    table_stats = self._get_table_stats(session)
                except Exception as e:
                    logger.warning(f"Error getting table stats: {e}")
                    try:
                        session.rollback()
                    except Exception:
                        pass
                
                metrics = DBMetrics(
                    active_connections=connections['active'],
                    total_connections=connections['total'],
                    max_connections=connections['max'],
                    queries_per_second=performance['qps'],
                    avg_query_time=performance['avg_time'],
                    slow_queries_count=performance['slow_queries'],
                    database_size=resources['db_size'],
                    cache_hit_ratio=resources['cache_hit_ratio'],
                    index_hit_ratio=resources['index_hit_ratio'],
                    locks_count=locks['total_locks'],
                    waiting_queries=locks['waiting'],
                    table_stats=table_stats,
                    timestamp=datetime.now()
                )
                
                # Добавляем в историю
                self._add_to_history(metrics)
                
                return metrics
                
        except Exception as e:
            logger.error(f"Critical error collecting DB metrics: {e}")
            # Возвращаем базовые метрики вместо падения
            return DBMetrics(
                active_connections=0,
                total_connections=0,
                max_connections=0,
                queries_per_second=0.0,
                avg_query_time=0.0,
                slow_queries_count=0,
                database_size=0,
                cache_hit_ratio=0.0,
                index_hit_ratio=0.0,
                locks_count=0,
                waiting_queries=0,
                table_stats=[],
                timestamp=datetime.now()
            )
    
    def _get_connection_stats(self, session: Session) -> Dict[str, int]:
        """Получить статистику соединений"""
        try:
            query = text("""
                SELECT 
                    count(*) FILTER (WHERE state = 'active') as active,
                    count(*) as total,
                    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_conn
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)
            
            result = session.exec(query).first()
            return {
                'active': result[0] or 0,
                'total': result[1] or 0,
                'max': result[2] or 0
            }
        except Exception as e:
            logger.warning(f"Error getting connection stats: {e}")
            # Откатываем транзакцию
            try:
                session.rollback()
            except Exception:
                pass
            return {
                'active': 0,
                'total': 0,
                'max': 0
            }
    
    def _get_performance_stats(self, session: Session) -> Dict[str, float]:
        """Получить статистику производительности"""
        try:
            # Сначала попробуем pg_stat_statements
            qps_query = text("""
                SELECT 
                    COALESCE(sum(calls), 0) / GREATEST(extract(epoch from (now() - stats_reset)), 1) as qps,
                    COALESCE(avg(mean_exec_time), 0) as avg_time,
                    COALESCE(sum(calls) FILTER (WHERE mean_exec_time > 1000), 0) as slow_queries
                FROM pg_stat_statements 
                WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
            """)
            
            result = session.exec(qps_query).first()
            if result:
                return {
                    'qps': float(result[0] or 0),
                    'avg_time': float(result[1] or 0),
                    'slow_queries': int(result[2] or 0)
                }
        except Exception as e:
            logger.warning(f"pg_stat_statements not available: {e}")
            # Откатываем транзакцию если она была прервана
            try:
                session.rollback()
            except Exception:
                pass
        
        # Fallback к базовой статистике
        try:
            basic_query = text("""
                SELECT 
                    COALESCE(sum(numbackends), 0) as connections,
                    COALESCE(sum(tup_returned + tup_fetched), 0) as total_tuples
                FROM pg_stat_database 
                WHERE datname = current_database()
            """)
            
            result = session.exec(basic_query).first()
            if result:
                return {
                    'qps': float(result[1] or 0) / 60,  # Примерная оценка
                    'avg_time': 0.0,
                    'slow_queries': 0
                }
        except Exception as e:
            logger.error(f"Error getting basic performance stats: {e}")
            # Откатываем транзакцию если она была прервана
            try:
                session.rollback()
            except Exception:
                pass
        
        # Возвращаем нулевые значения если все запросы не удались
        return {
            'qps': 0.0,
            'avg_time': 0.0,
            'slow_queries': 0
        }
    
    def _get_resource_stats(self, session: Session) -> Dict[str, Any]:
        """Получить статистику использования ресурсов"""
        size_query = text("""
            SELECT pg_database_size(current_database()) as db_size
        """)
        
        cache_query = text("""
            SELECT 
                CASE 
                    WHEN (blks_hit + blks_read) > 0 
                    THEN round(100.0 * blks_hit / (blks_hit + blks_read), 2)
                    ELSE 0 
                END as cache_hit_ratio
            FROM pg_stat_database 
            WHERE datname = current_database()
        """)
        
        index_query = text("""
            SELECT 
                CASE 
                    WHEN (idx_blks_hit + idx_blks_read) > 0 
                    THEN round(100.0 * idx_blks_hit / (idx_blks_hit + idx_blks_read), 2)
                    ELSE 0 
                END as index_hit_ratio
            FROM pg_statio_user_indexes
        """)
        
        db_size = session.exec(size_query).scalar() or 0
        cache_hit = session.exec(cache_query).scalar() or 0.0
        
        try:
            index_hit = session.exec(index_query).scalar() or 0.0
        except Exception:
            index_hit = 0.0
        
        return {
            'db_size': int(db_size),
            'cache_hit_ratio': float(cache_hit),
            'index_hit_ratio': float(index_hit)
        }
    
    def _get_lock_stats(self, session: Session) -> Dict[str, int]:
        """Получить статистику блокировок"""
        locks_query = text("""
            SELECT 
                count(*) as total_locks,
                count(*) FILTER (WHERE NOT granted) as waiting
            FROM pg_locks 
            WHERE database = (SELECT oid FROM pg_database WHERE datname = current_database())
        """)
        
        result = session.exec(locks_query).first()
        return {
            'total_locks': result[0] or 0,
            'waiting': result[1] or 0
        }
    
    def _get_table_stats(self, session: Session) -> List[Dict[str, Any]]:
        """Получить статистику по таблицам"""
        query = text("""
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_tup_hot_upd as hot_updates,
                n_live_tup as live_tuples,
                n_dead_tup as dead_tuples,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables 
            ORDER BY (n_tup_ins + n_tup_upd + n_tup_del) DESC
            LIMIT 10
        """)
        
        results = session.exec(query).all()
        return [
            {
                'schema': row[0],
                'table': row[1],
                'inserts': row[2] or 0,
                'updates': row[3] or 0,
                'deletes': row[4] or 0,
                'hot_updates': row[5] or 0,
                'live_tuples': row[6] or 0,
                'dead_tuples': row[7] or 0,
                'last_vacuum': row[8].isoformat() if row[8] else None,
                'last_autovacuum': row[9].isoformat() if row[9] else None,
                'last_analyze': row[10].isoformat() if row[10] else None,
                'last_autoanalyze': row[11].isoformat() if row[11] else None,
            }
            for row in results
        ]
    
    def _add_to_history(self, metrics: DBMetrics):
        """Добавить метрики в историю"""
        self.metrics_history.append(metrics)
        
        # Ограничиваем размер истории
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    def get_metrics_history(self, hours: int = 1) -> List[DBMetrics]:
        """Получить историю метрик за указанное количество часов"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            metrics for metrics in self.metrics_history 
            if metrics.timestamp >= cutoff
        ]
    
    def get_current_metrics(self) -> Optional[DBMetrics]:
        """Получить последние собранные метрики"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_alert_conditions(self, metrics: DBMetrics) -> List[str]:
        """Проверить условия для алертов"""
        alerts = []
        
        # Высокое использование соединений
        if metrics.max_connections > 0:
            connection_usage = (metrics.active_connections / metrics.max_connections) * 100
            if connection_usage > 80:
                alerts.append(f"Высокое использование соединений: {connection_usage:.1f}%")
        
        # Низкий cache hit ratio
        if metrics.cache_hit_ratio < 90:
            alerts.append(f"Низкий cache hit ratio: {metrics.cache_hit_ratio:.1f}%")
        
        # Много медленных запросов
        if metrics.slow_queries_count > 10:
            alerts.append(f"Много медленных запросов: {metrics.slow_queries_count}")
        
        # Ожидающие запросы
        if metrics.waiting_queries > 5:
            alerts.append(f"Запросы в ожидании блокировок: {metrics.waiting_queries}")
        
        # Высокое среднее время запроса
        if metrics.avg_query_time > 1000:  # более 1 секунды
            alerts.append(f"Высокое среднее время запроса: {metrics.avg_query_time:.1f}ms")
        
        return alerts
    
    def format_size(self, size_bytes: int) -> str:
        """Форматировать размер в человекочитаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


# Глобальный экземпляр монитора
db_monitor = DatabaseMonitor()