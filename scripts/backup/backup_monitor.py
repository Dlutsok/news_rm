#!/usr/bin/env python3

"""
PostgreSQL Backup Monitor for Medical News Automation System
Мониторинг состояния backup'ов и отправка уведомлений
"""

import os
import sys
import json
import datetime
import glob
import subprocess
import gzip
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackupMonitor:
    """Класс для мониторинга backup'ов PostgreSQL"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.backup_dir = self.config.get('backup_dir', '/var/backups/postgres/medical-news')
        
    def _load_config(self, config_file: Optional[str] = None) -> Dict:
        """Загрузка конфигурации из файла или переменных окружения"""
        config = {}
        
        # Загрузка из .env файла
        env_file = Path(__file__).parent.parent.parent / '.env'
        if env_file.exists():
            try:
                with open(env_file) as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
            except Exception as e:
                logger.warning(f"Не удалось загрузить .env файл: {e}")
        
        # Конфигурация из переменных окружения
        config.update({
            'backup_dir': os.getenv('BACKUP_DIR', '/var/backups/postgres/medical-news'),
            'database_url': os.getenv('DATABASE_URL', ''),
            'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
            'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
            'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL', ''),
            'backup_retention_days': int(os.getenv('BACKUP_RETENTION_DAYS', '7')),
            'backup_retention_weeks': int(os.getenv('BACKUP_RETENTION_WEEKS', '4')),
            'backup_retention_months': int(os.getenv('BACKUP_RETENTION_MONTHS', '12')),
        })
        
        # Загрузка из JSON файла (если указан)
        if config_file and Path(config_file).exists():
            try:
                with open(config_file) as f:
                    config.update(json.load(f))
            except Exception as e:
                logger.warning(f"Не удалось загрузить config файл {config_file}: {e}")
        
        return config
    
    def check_backup_freshness(self) -> Dict[str, any]:
        """Проверка свежести backup'ов"""
        results = {
            'daily': {'status': 'unknown', 'last_backup': None, 'age_hours': None},
            'weekly': {'status': 'unknown', 'last_backup': None, 'age_hours': None},
            'monthly': {'status': 'unknown', 'last_backup': None, 'age_hours': None}
        }
        
        backup_types = {
            'daily': {'max_age_hours': 26, 'pattern': 'medical_news_daily_*.sql.gz'},
            'weekly': {'max_age_hours': 7 * 24 + 2, 'pattern': 'medical_news_weekly_*.sql.gz'},
            'monthly': {'max_age_hours': 32 * 24, 'pattern': 'medical_news_monthly_*.sql.gz'}
        }
        
        for backup_type, config in backup_types.items():
            backup_path = Path(self.backup_dir) / backup_type
            
            if not backup_path.exists():
                results[backup_type]['status'] = 'missing_directory'
                continue
            
            # Поиск самого свежего backup'а
            pattern = str(backup_path / config['pattern'])
            backup_files = glob.glob(pattern)
            
            if not backup_files:
                results[backup_type]['status'] = 'no_backups'
                continue
            
            # Находим самый новый файл
            latest_backup = max(backup_files, key=os.path.getmtime)
            backup_time = datetime.datetime.fromtimestamp(os.path.getmtime(latest_backup))
            age_hours = (datetime.datetime.now() - backup_time).total_seconds() / 3600
            
            results[backup_type]['last_backup'] = latest_backup
            results[backup_type]['age_hours'] = age_hours
            
            if age_hours <= config['max_age_hours']:
                results[backup_type]['status'] = 'fresh'
            else:
                results[backup_type]['status'] = 'stale'
        
        return results
    
    def verify_backup_integrity(self, backup_file: str) -> Dict[str, any]:
        """Проверка целостности backup файла"""
        result = {
            'file': backup_file,
            'status': 'unknown',
            'file_size': 0,
            'error': None
        }
        
        try:
            # Проверка существования файла
            if not os.path.exists(backup_file):
                result['status'] = 'missing'
                result['error'] = 'File does not exist'
                return result
            
            # Размер файла
            result['file_size'] = os.path.getsize(backup_file)
            
            if result['file_size'] == 0:
                result['status'] = 'empty'
                result['error'] = 'File is empty'
                return result
            
            # Проверка gzip архива
            try:
                with gzip.open(backup_file, 'rt') as f:
                    # Читаем первые несколько строк
                    header = f.read(1000)
                    if 'PostgreSQL database dump' not in header:
                        result['status'] = 'invalid'
                        result['error'] = 'Not a valid PostgreSQL dump'
                        return result
            except Exception as e:
                result['status'] = 'corrupted'
                result['error'] = f'Gzip error: {str(e)}'
                return result
            
            result['status'] = 'valid'
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def get_backup_statistics(self) -> Dict[str, any]:
        """Получение статистики по backup'ам"""
        stats = {
            'daily': {'count': 0, 'total_size': 0, 'valid': 0, 'invalid': 0},
            'weekly': {'count': 0, 'total_size': 0, 'valid': 0, 'invalid': 0},
            'monthly': {'count': 0, 'total_size': 0, 'valid': 0, 'invalid': 0},
            'pre_restore': {'count': 0, 'total_size': 0, 'valid': 0, 'invalid': 0}
        }
        
        for backup_type in stats.keys():
            backup_path = Path(self.backup_dir) / backup_type
            
            if not backup_path.exists():
                continue
            
            pattern = str(backup_path / 'medical_news_*.sql.gz')
            backup_files = glob.glob(pattern)
            
            stats[backup_type]['count'] = len(backup_files)
            
            for backup_file in backup_files:
                try:
                    file_size = os.path.getsize(backup_file)
                    stats[backup_type]['total_size'] += file_size
                    
                    # Быстрая проверка целостности
                    if file_size > 0:
                        try:
                            with gzip.open(backup_file, 'rt') as f:
                                f.read(100)  # Попытка прочитать начало
                            stats[backup_type]['valid'] += 1
                        except:
                            stats[backup_type]['invalid'] += 1
                    else:
                        stats[backup_type]['invalid'] += 1
                        
                except Exception:
                    stats[backup_type]['invalid'] += 1
        
        return stats
    
    def check_disk_space(self) -> Dict[str, any]:
        """Проверка свободного места на диске"""
        result = {
            'backup_dir': self.backup_dir,
            'available_gb': 0,
            'used_gb': 0,
            'total_gb': 0,
            'usage_percent': 0,
            'status': 'unknown'
        }
        
        try:
            statvfs = os.statvfs(self.backup_dir)
            
            # Вычисление размеров в GB
            total_size = statvfs.f_frsize * statvfs.f_blocks
            available_size = statvfs.f_frsize * statvfs.f_bavail
            used_size = total_size - available_size
            
            result['available_gb'] = round(available_size / (1024**3), 2)
            result['used_gb'] = round(used_size / (1024**3), 2)
            result['total_gb'] = round(total_size / (1024**3), 2)
            result['usage_percent'] = round((used_size / total_size) * 100, 1)
            
            # Определение статуса
            if result['usage_percent'] < 80:
                result['status'] = 'ok'
            elif result['usage_percent'] < 90:
                result['status'] = 'warning'
            else:
                result['status'] = 'critical'
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def send_notification(self, message: str, status: str = 'INFO') -> bool:
        """Отправка уведомлений в Telegram и Slack"""
        success = True
        
        # Telegram
        if self.config.get('telegram_bot_token') and self.config.get('telegram_chat_id'):
            success &= self._send_telegram(message, status)
        
        # Slack
        if self.config.get('slack_webhook_url'):
            success &= self._send_slack(message, status)
        
        return success
    
    def _send_telegram(self, message: str, status: str) -> bool:
        """Отправка сообщения в Telegram"""
        try:
            emoji_map = {
                'SUCCESS': '✅',
                'ERROR': '❌', 
                'WARNING': '⚠️',
                'INFO': 'ℹ️'
            }
            
            emoji = emoji_map.get(status, 'ℹ️')
            full_message = f"{emoji} Medical News DB Backup Monitor: {message}"
            
            url = f"https://api.telegram.org/bot{self.config['telegram_bot_token']}/sendMessage"
            data = {
                'chat_id': self.config['telegram_chat_id'],
                'text': full_message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.info("Telegram уведомление отправлено")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки Telegram уведомления: {e}")
            return False
    
    def _send_slack(self, message: str, status: str) -> bool:
        """Отправка сообщения в Slack"""
        try:
            color_map = {
                'SUCCESS': 'good',
                'ERROR': 'danger',
                'WARNING': 'warning',
                'INFO': '#36a64f'
            }
            
            color = color_map.get(status, '#36a64f')
            
            payload = {
                'attachments': [{
                    'color': color,
                    'text': f"Medical News DB Backup Monitor: {message}"
                }]
            }
            
            response = requests.post(
                self.config['slack_webhook_url'],
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("Slack уведомление отправлено")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки Slack уведомления: {e}")
            return False
    
    def generate_report(self) -> Dict[str, any]:
        """Генерация полного отчета о состоянии backup'ов"""
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'backup_freshness': self.check_backup_freshness(),
            'backup_statistics': self.get_backup_statistics(),
            'disk_space': self.check_disk_space(),
            'issues': [],
            'overall_status': 'ok'
        }
        
        # Анализ проблем
        issues = []
        
        # Проверка свежести backup'ов
        for backup_type, data in report['backup_freshness'].items():
            if data['status'] in ['no_backups', 'missing_directory']:
                issues.append(f"Отсутствуют {backup_type} backup'ы")
            elif data['status'] == 'stale':
                issues.append(f"{backup_type.capitalize()} backup устарел ({data['age_hours']:.1f} часов)")
        
        # Проверка места на диске
        disk_data = report['disk_space']
        if disk_data['status'] == 'critical':
            issues.append(f"Критически мало места на диске ({disk_data['usage_percent']}%)")
        elif disk_data['status'] == 'warning':
            issues.append(f"Мало места на диске ({disk_data['usage_percent']}%)")
        
        # Проверка поврежденных backup'ов
        stats = report['backup_statistics']
        for backup_type, data in stats.items():
            if data['invalid'] > 0:
                issues.append(f"Найдены поврежденные {backup_type} backup'ы: {data['invalid']}")
        
        report['issues'] = issues
        
        # Общий статус
        if any('Критически' in issue for issue in issues):
            report['overall_status'] = 'critical'
        elif any('Отсутствуют' in issue or 'устарел' in issue for issue in issues):
            report['overall_status'] = 'error'
        elif issues:
            report['overall_status'] = 'warning'
        
        return report
    
    def monitor_and_alert(self, send_alerts: bool = True) -> Dict[str, any]:
        """Основная функция мониторинга с отправкой алертов"""
        logger.info("Запуск мониторинга backup'ов...")
        
        report = self.generate_report()
        
        # Отправка уведомлений при проблемах
        if send_alerts and report['issues']:
            status_map = {
                'critical': 'ERROR',
                'error': 'ERROR', 
                'warning': 'WARNING'
            }
            
            status = status_map.get(report['overall_status'], 'INFO')
            message = f"Обнаружены проблемы с backup'ами:\n" + "\n".join(f"• {issue}" for issue in report['issues'])
            
            self.send_notification(message, status)
        
        return report


def main():
    """Основная функция для запуска из командной строки"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PostgreSQL Backup Monitor')
    parser.add_argument('--config', help='Путь к файлу конфигурации')
    parser.add_argument('--no-alerts', action='store_true', help='Не отправлять уведомления')
    parser.add_argument('--json', action='store_true', help='Вывод в формате JSON')
    parser.add_argument('--verify', help='Проверить конкретный backup файл')
    
    args = parser.parse_args()
    
    monitor = BackupMonitor(args.config)
    
    if args.verify:
        # Проверка конкретного файла
        result = monitor.verify_backup_integrity(args.verify)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Файл: {result['file']}")
            print(f"Статус: {result['status']}")
            print(f"Размер: {result['file_size']} байт")
            if result['error']:
                print(f"Ошибка: {result['error']}")
        
        sys.exit(0 if result['status'] == 'valid' else 1)
    
    # Полный мониторинг
    report = monitor.monitor_and_alert(send_alerts=not args.no_alerts)
    
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        # Человеко-читаемый вывод
        print(f"=== Отчет о состоянии backup'ов ===")
        print(f"Время: {report['timestamp']}")
        print(f"Общий статус: {report['overall_status'].upper()}")
        print()
        
        # Свежесть backup'ов
        print("Свежесть backup'ов:")
        for backup_type, data in report['backup_freshness'].items():
            status_emoji = {
                'fresh': '✅',
                'stale': '⚠️',
                'no_backups': '❌',
                'missing_directory': '❌',
                'unknown': '❓'
            }
            emoji = status_emoji.get(data['status'], '❓')
            print(f"  {emoji} {backup_type}: {data['status']}")
            if data['age_hours'] is not None:
                print(f"    Возраст: {data['age_hours']:.1f} часов")
        
        print()
        
        # Статистика
        print("Статистика backup'ов:")
        stats = report['backup_statistics']
        for backup_type, data in stats.items():
            if data['count'] > 0:
                size_mb = data['total_size'] / (1024 * 1024)
                print(f"  {backup_type}: {data['count']} файлов, {size_mb:.1f} MB")
                if data['invalid'] > 0:
                    print(f"    ⚠️ Поврежденных: {data['invalid']}")
        
        print()
        
        # Место на диске
        disk = report['disk_space']
        status_emoji = {'ok': '✅', 'warning': '⚠️', 'critical': '❌', 'error': '❓'}
        emoji = status_emoji.get(disk['status'], '❓')
        print(f"Место на диске: {emoji}")
        print(f"  Использовано: {disk['used_gb']} GB / {disk['total_gb']} GB ({disk['usage_percent']}%)")
        print(f"  Доступно: {disk['available_gb']} GB")
        
        if report['issues']:
            print()
            print("Обнаруженные проблемы:")
            for issue in report['issues']:
                print(f"  ❌ {issue}")
    
    # Возвращаем код ошибки в зависимости от статуса
    exit_codes = {
        'ok': 0,
        'warning': 1,
        'error': 2,
        'critical': 3
    }
    
    sys.exit(exit_codes.get(report['overall_status'], 0))


if __name__ == '__main__':
    main()