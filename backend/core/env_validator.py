"""
Валидатор переменных окружения для проверки критически важных настроек при старте сервисов
"""

import os
import re
import sys
import logging
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Уровни валидации переменных окружения"""
    REQUIRED = "required"  # Обязательная переменная - без неё сервис не запустится
    IMPORTANT = "important"  # Важная переменная - показать предупреждение если отсутствует
    OPTIONAL = "optional"  # Опциональная переменная - только для информации


class EnvVariable:
    """Описание переменной окружения для валидации"""
    
    def __init__(
        self,
        name: str,
        level: ValidationLevel,
        description: str,
        validator: Optional[Callable[[str], bool]] = None,
        default_value: Optional[str] = None,
        example: Optional[str] = None
    ):
        self.name = name
        self.level = level
        self.description = description
        self.validator = validator or (lambda x: bool(x.strip()))
        self.default_value = default_value
        self.example = example


class EnvValidator:
    """Валидатор переменных окружения"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.variables: List[EnvVariable] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def add_variable(self, variable: EnvVariable):
        """Добавить переменную для валидации"""
        self.variables.append(variable)
        
    def add_required(self, name: str, description: str, validator: Optional[Callable[[str], bool]] = None, example: Optional[str] = None):
        """Добавить обязательную переменную"""
        self.add_variable(EnvVariable(name, ValidationLevel.REQUIRED, description, validator, example=example))
        
    def add_important(self, name: str, description: str, default_value: Optional[str] = None, validator: Optional[Callable[[str], bool]] = None):
        """Добавить важную переменную"""
        self.add_variable(EnvVariable(name, ValidationLevel.IMPORTANT, description, validator, default_value))
        
    def add_optional(self, name: str, description: str, default_value: Optional[str] = None):
        """Добавить опциональную переменную"""
        self.add_variable(EnvVariable(name, ValidationLevel.OPTIONAL, description, default_value=default_value))
        
    def validate(self) -> bool:
        """
        Выполнить валидацию всех переменных
        
        Returns:
            bool: True если все обязательные переменные валидны, False если есть критические ошибки
        """
        self.errors.clear()
        self.warnings.clear()
        
        logger.info(f"🔍 Валидация переменных окружения для {self.service_name}")
        
        for var in self.variables:
            self._validate_variable(var)
            
        # Выводим результаты
        self._print_results()
        
        # Возвращаем False если есть критические ошибки
        return len(self.errors) == 0
        
    def _validate_variable(self, var: EnvVariable):
        """Валидировать одну переменную"""
        value = os.getenv(var.name, "").strip()
        
        if not value:
            if var.level == ValidationLevel.REQUIRED:
                message = f"❌ КРИТИЧЕСКАЯ ОШИБКА: {var.name} не задана! {var.description}"
                if var.example:
                    message += f" Пример: {var.example}"
                self.errors.append(message)
            elif var.level == ValidationLevel.IMPORTANT:
                message = f"⚠️  ПРЕДУПРЕЖДЕНИЕ: {var.name} не задана. {var.description}"
                if var.default_value:
                    message += f" Используется значение по умолчанию: {var.default_value}"
                self.warnings.append(message)
            # OPTIONAL переменные не генерируют сообщений если отсутствуют
            return
            
        # Если значение есть, проверяем валидатором
        try:
            if not var.validator(value):
                message = f"❌ ОШИБКА ВАЛИДАЦИИ: {var.name} имеет некорректное значение. {var.description}"
                if var.level == ValidationLevel.REQUIRED:
                    self.errors.append(message)
                else:
                    self.warnings.append(message)
        except Exception as e:
            message = f"❌ ОШИБКА ВАЛИДАЦИИ: {var.name} - ошибка валидатора: {e}"
            if var.level == ValidationLevel.REQUIRED:
                self.errors.append(message)
            else:
                self.warnings.append(message)
                
    def _print_results(self):
        """Вывести результаты валидации"""
        print(f"\n{'='*60}")
        print(f"📋 РЕЗУЛЬТАТ ВАЛИДАЦИИ: {self.service_name}")
        print(f"{'='*60}")
        
        if not self.errors and not self.warnings:
            print("✅ Все переменные окружения корректно настроены!")
            return
            
        if self.errors:
            print(f"\n🚨 КРИТИЧЕСКИЕ ОШИБКИ ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
                
        if self.warnings:
            print(f"\n⚠️  ПРЕДУПРЕЖДЕНИЯ ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
                
        if self.errors:
            print(f"\n❌ СЕРВИС НЕ МОЖЕТ БЫТЬ ЗАПУЩЕН!")
            print("Исправьте критические ошибки в .env файле и перезапустите.")
        else:
            print(f"\n✅ Сервис может быть запущен, но рекомендуется исправить предупреждения.")
            
    def validate_and_exit_on_error(self):
        """Валидировать и завершить процесс при критических ошибках"""
        if not self.validate():
            print(f"\n💥 {self.service_name} завершает работу из-за критических ошибок конфигурации!")
            sys.exit(1)


# Готовые валидаторы для популярных типов переменных

def validate_url(url: str) -> bool:
    """Валидатор для URL"""
    if not url.strip():
        return False
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(url))


def validate_postgresql_url(url: str) -> bool:
    """Валидатор для PostgreSQL URL"""
    if not url.strip():
        return False
    return url.startswith(('postgresql://', 'postgres://'))


def validate_non_default_secret(secret: str) -> bool:
    """Валидатор для секретных ключей - не должны быть дефолтными"""
    if not secret.strip():
        return False
    dangerous_defaults = [
        'your-secret-key',
        'change-in-production', 
        'your_openai_api_key_here',
        'your-jwt-secret-key'
    ]
    return not any(danger in secret.lower() for danger in dangerous_defaults)


def validate_openai_key(key: str) -> bool:
    """Валидатор для OpenAI API ключа"""
    if not key.strip():
        return False
    return key.startswith('sk-') and len(key) > 20


def validate_kie_key(key: str) -> bool:
    """Валидатор для KIE AI API ключа"""
    if not key.strip():
        return False
    return len(key) > 10  # Простая проверка длины


def validate_boolean_env(value: str) -> bool:
    """Валидатор для boolean переменных"""
    return value.lower() in ('true', 'false', '1', '0', 'yes', 'no')


def validate_port(port: str) -> bool:
    """Валидатор для портов"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False


# Готовые конфигурации валидаторов для каждого сервиса

def create_backend_validator() -> EnvValidator:
    """Создать валидатор для backend сервиса"""
    validator = EnvValidator("Backend Service")
    
    # Критически важные переменные
    validator.add_required(
        "DATABASE_URL", 
        "URL подключения к PostgreSQL базе данных",
        validate_postgresql_url,
        "postgresql://user:password@localhost:5432/news_aggregator"
    )
    
    validator.add_required(
        "JWT_SECRET_KEY",
        "Секретный ключ для JWT токенов (должен быть уникальным в продакшене)",
        validate_non_default_secret,
        "dWiwTuG1vHPThqTiJhq-rfk691-L1tVDzCaJS_wvm6u..."
    )
    
    validator.add_required(
        "SECRET_KEY",
        "Основной секретный ключ приложения (должен быть уникальным в продакшене)",
        validate_non_default_secret,
        "vGaQTU-xp-FBOQmZy8CKaBi7Putr6tSICrnNa9tk5L8"
    )
    
    validator.add_required(
        "OPENAI_API_KEY",
        "API ключ OpenAI для генерации контента",
        validate_openai_key,
        "sk-proj-..."
    )

    # Переменные для генерации изображений (KIE AI)
    validator.add_important(
        "KIE_API_KEY",
        "KIE AI API ключ для генерации изображений (Nano Banana - Google Gemini 2.5 Flash)",
        default_value=None
    )

    validator.add_optional(
        "KIE_API_BASE_URL",
        "KIE AI API base URL",
        default_value="https://api.kie.ai/api/v1"
    )

    validator.add_optional(
        "KIE_TIMEOUT",
        "Timeout для KIE AI в секундах",
        default_value="300"
    )
    
    # Важные переменные
    validator.add_important(
        "ADMIN_USERNAME",
        "Имя пользователя администратора",
        "admin"
    )
    
    validator.add_important(
        "ADMIN_PASSWORD", 
        "Пароль администратора (рекомендуется сменить дефолтный)",
        "admin123"
    )
    
    validator.add_important(
        "CORS_ORIGINS",
        "Разрешенные домены для CORS (критично для безопасности)",
        "http://localhost:3000"
    )
    
    # Опциональные
    validator.add_optional("DEBUG", "Режим отладки", "False")
    validator.add_optional("HOST", "Хост сервера", "0.0.0.0")
    validator.add_optional("PORT", "Порт сервера", "8000")
    
    return validator




