"""
Модуль для мониторинга системных ресурсов и сервисов
"""

import psutil
import logging
import asyncio
import aiohttp
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import os

logger = logging.getLogger(__name__)


@dataclass
class ServiceStatus:
    """Статус сервиса"""
    name: str
    url: str
    status: str  # healthy, warning, critical, unknown
    response_time: float
    last_check: datetime
    error_message: Optional[str] = None


@dataclass
class SystemMetrics:
    """Системные метрики"""
    cpu_percent: float
    memory_total: int
    memory_used: int
    memory_percent: float
    disk_total: int
    disk_used: int
    disk_percent: float
    network_sent: int
    network_recv: int
    uptime: float
    timestamp: datetime


@dataclass
class Alert:
    """Системный алерт"""
    id: str
    type: str  # critical, warning, info
    title: str
    message: str
    service: str
    timestamp: datetime
    acknowledged: bool = False


class SystemMonitor:
    """Класс для мониторинга системы"""
    
    def __init__(self):
        self.services = [
            {
                'name': 'Backend API',
                'url': 'http://localhost:8000/health',
                'timeout': 5
            },
            {
                'name': 'Image Generation',
                'url': 'http://localhost:8000/api/images/health',
                'timeout': 10
            },
            {
                'name': 'Frontend',
                'url': 'http://localhost:3000/',
                'timeout': 5
            }
        ]
        
        self.alerts: List[Alert] = []
        self.service_statuses: Dict[str, ServiceStatus] = {}
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 100
        
        # Пороговые значения для алертов
        self.thresholds = {
            'cpu_critical': 90.0,
            'cpu_warning': 75.0,
            'memory_critical': 90.0,
            'memory_warning': 80.0,
            'disk_critical': 95.0,
            'disk_warning': 85.0,
            'response_time_critical': 5000.0,  # 5 секунд
            'response_time_warning': 1000.0    # 1 секунда
        }
    
    async def check_service_health(self, service: Dict[str, Any]) -> ServiceStatus:
        """Проверить здоровье одного сервиса"""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=service.get('timeout', 5))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(service['url']) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    # Определяем базовый статус по HTTP коду
                    if 200 <= response.status <= 299:
                        status = 'healthy'
                        error_message = None
                        
                        # Проверяем время ответа только для успешных запросов
                        if response_time > self.thresholds['response_time_critical']:
                            status = 'critical'
                            error_message = f"Очень медленный ответ: {response_time:.1f}ms"
                        elif response_time > self.thresholds['response_time_warning']:
                            status = 'warning'
                            error_message = f"Медленный ответ: {response_time:.1f}ms"
                    else:
                        status = 'critical'
                        error_message = f"HTTP {response.status}"
                    
                    return ServiceStatus(
                        name=service['name'],
                        url=service['url'],
                        status=status,
                        response_time=response_time,
                        last_check=datetime.now(),
                        error_message=error_message
                    )
                    
        except asyncio.TimeoutError:
            return ServiceStatus(
                name=service['name'],
                url=service['url'],
                status='critical',
                response_time=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                error_message="Request timeout"
            )
        except Exception as e:
            return ServiceStatus(
                name=service['name'],
                url=service['url'],
                status='critical',
                response_time=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def check_all_services(self) -> Dict[str, ServiceStatus]:
        """Проверить все сервисы параллельно"""
        tasks = [self.check_service_health(service) for service in self.services]
        statuses = await asyncio.gather(*tasks)
        
        # Обновляем статусы сервисов
        for status in statuses:
            self.service_statuses[status.name] = status
            
            # Генерируем алерты при проблемах
            if status.status == 'critical':
                self._add_alert(
                    type='critical',
                    title=f'Сервис {status.name} недоступен',
                    message=f'Ошибка: {status.error_message}',
                    service=status.name
                )
            elif status.status == 'warning':
                self._add_alert(
                    type='warning',
                    title=f'Медленный ответ от {status.name}',
                    message=f'Время ответа: {status.response_time:.1f}ms',
                    service=status.name
                )
        
        return self.service_statuses
    
    def get_system_metrics(self) -> SystemMetrics:
        """Получить системные метрики"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory
            memory = psutil.virtual_memory()
            
            # Disk (используем корневую директорию)
            disk = psutil.disk_usage('/')
            
            # Network
            network = psutil.net_io_counters()
            
            # Uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_total=memory.total,
                memory_used=memory.used,
                memory_percent=memory.percent,
                disk_total=disk.total,
                disk_used=disk.used,
                disk_percent=(disk.used / disk.total) * 100,
                network_sent=network.bytes_sent,
                network_recv=network.bytes_recv,
                uptime=uptime,
                timestamp=datetime.now()
            )
            
            # Добавляем в историю
            self._add_to_history(metrics)
            
            # Проверяем пороговые значения
            self._check_system_thresholds(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            raise
    
    def _add_to_history(self, metrics: SystemMetrics):
        """Добавить метрики в историю"""
        self.metrics_history.append(metrics)
        
        # Ограничиваем размер истории
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    def _check_system_thresholds(self, metrics: SystemMetrics):
        """Проверить пороговые значения системных метрик"""
        # CPU
        if metrics.cpu_percent >= self.thresholds['cpu_critical']:
            self._add_alert(
                type='critical',
                title='Критическая загрузка CPU',
                message=f'CPU: {metrics.cpu_percent:.1f}%',
                service='System'
            )
        elif metrics.cpu_percent >= self.thresholds['cpu_warning']:
            self._add_alert(
                type='warning',
                title='Высокая загрузка CPU',
                message=f'CPU: {metrics.cpu_percent:.1f}%',
                service='System'
            )
        
        # Memory
        if metrics.memory_percent >= self.thresholds['memory_critical']:
            self._add_alert(
                type='critical',
                title='Критическое использование памяти',
                message=f'RAM: {metrics.memory_percent:.1f}%',
                service='System'
            )
        elif metrics.memory_percent >= self.thresholds['memory_warning']:
            self._add_alert(
                type='warning',
                title='Высокое использование памяти',
                message=f'RAM: {metrics.memory_percent:.1f}%',
                service='System'
            )
        
        # Disk
        if metrics.disk_percent >= self.thresholds['disk_critical']:
            self._add_alert(
                type='critical',
                title='Критическое заполнение диска',
                message=f'Диск: {metrics.disk_percent:.1f}%',
                service='System'
            )
        elif metrics.disk_percent >= self.thresholds['disk_warning']:
            self._add_alert(
                type='warning',
                title='Высокое заполнение диска',
                message=f'Диск: {metrics.disk_percent:.1f}%',
                service='System'
            )
    
    def _add_alert(self, type: str, title: str, message: str, service: str):
        """Добавить алерт"""
        # Избегаем дублирования алертов
        recent_alerts = [
            alert for alert in self.alerts
            if alert.title == title and alert.service == service
            and (datetime.now() - alert.timestamp).seconds < 300  # 5 минут
        ]
        
        if not recent_alerts:
            alert = Alert(
                id=f"{int(time.time())}-{hash(title + service) % 10000}",
                type=type,
                title=title,
                message=message,
                service=service,
                timestamp=datetime.now()
            )
            self.alerts.append(alert)
            
            # Ограничиваем количество алертов
            if len(self.alerts) > 50:
                self.alerts = self.alerts[-50:]
    
    def get_active_alerts(self) -> List[Alert]:
        """Получить активные (неподтвержденные) алерты"""
        return [alert for alert in self.alerts if not alert.acknowledged]
    
    def get_all_alerts(self, limit: int = 20) -> List[Alert]:
        """Получить все алерты"""
        return sorted(self.alerts, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Подтвердить алерт"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def get_metrics_history(self, hours: int = 1) -> List[SystemMetrics]:
        """Получить историю метрик за указанное количество часов"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            metrics for metrics in self.metrics_history
            if metrics.timestamp >= cutoff
        ]
    
    def format_bytes(self, bytes_value: int) -> str:
        """Форматировать байты в человекочитаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def format_uptime(self, seconds: float) -> str:
        """Форматировать uptime в человекочитаемый вид"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        elif hours > 0:
            return f"{hours}ч {minutes}м"
        else:
            return f"{minutes}м"


# Глобальный экземпляр монитора
system_monitor = SystemMonitor()