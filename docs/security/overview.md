# Политики безопасности системы

## Обзор

Система медицинских новостей обрабатывает чувствительную информацию и интегрируется с внешними сервисами, что требует соблюдения строгих политик безопасности. Данный документ описывает меры защиты, применяемые на всех уровнях системы.

## Архитектура безопасности

### Уровни защиты

1. **Сетевой уровень**
   - Файрвол (UFW/iptables)
   - Ограничение доступа к портам
   - DDoS защита через Nginx
   - Rate limiting

2. **Уровень приложения**
   - Аутентификация и авторизация (JWT)
   - Валидация входных данных
   - CORS политики
   - SQL injection защита

3. **Уровень данных**
   - Шифрование в транзите (HTTPS/TLS)
   - Хеширование паролей (bcrypt)
   - Защита секретных ключей
   - Audit logging

4. **Инфраструктурный уровень**
   - Регулярные обновления ОС
   - Мониторинг безопасности
   - Backup шифрование
   - Access control

## Аутентификация и авторизация

### JWT (JSON Web Tokens)

**Настройки токенов:**
```python
JWT_SECRET_KEY = "очень_секретный_ключ_256_бит"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440  # 24 часа
```

**Ротация ключей:**
- Ключи меняются каждые 90 дней
- Поддерживается graceful transition
- Уведомление за 7 дней до смены

**Политики токенов:**
- Автоматическое истечение через 24 часа
- Blacklist для отозванных токенов
- Refresh token для продления сессии
- Secure flag для HTTPS только

### Ролевая модель

**Роли пользователей:**

1. **admin** - Полный доступ
   - Управление пользователями
   - Настройки системы
   - Просмотр всех данных
   - Системное администрирование

2. **staff** - Рабочий доступ
   - Создание и редактирование новостей
   - Публикация контента
   - Просмотр аналитики
   - Управление проектами

3. **analyst** - Только чтение
   - Просмотр статистики
   - Экспорт отчетов
   - Просмотр публикаций

**Матрица разрешений:**
```
Ресурс                  | admin | staff | analyst
------------------------|-------|-------|--------
/api/news/parse         |   ✓   |   ✓   |   ✗
/api/news/articles      |   ✓   |   ✓   |   ✓
/api/news-generation/*  |   ✓   |   ✓   |   ✗
/api/users              |   ✓   |   ✗   |   ✗
/api/admin/*            |   ✓   |   ✗   |   ✗
/api/expenses           |   ✓   |   ✓   |   ✓
/api/settings           |   ✓   |   ✗   |   ✗
```

## Защита от веб-атак

### OWASP Top 10 Защита

1. **Injection (SQL, NoSQL, OS)**
   - Использование SQLModel ORM
   - Параметризованные запросы
   - Валидация входных данных
   - Escape специальных символов

2. **Broken Authentication**
   - Надежные пароли (bcrypt + salt)
   - JWT с коротким TTL
   - Двухфакторная аутентификация (планируется)
   - Session management

3. **Sensitive Data Exposure**
   - HTTPS обязательно
   - Секреты в переменных окружения
   - Маскирование логов
   - Шифрование бэкапов

4. **XML External Entities (XXE)**
   - Отключение внешних entities
   - Валидация XML (если используется)
   - Safe parsing libraries

5. **Broken Access Control**
   - Проверка разрешений на каждом endpoint
   - Least privilege principle
   - Resource-based authorization
   - Path traversal защита

6. **Security Misconfiguration**
   - Регулярные security audits
   - Отключение debug в production
   - Удаление дефолтных паролей
   - Secure headers

7. **Cross-Site Scripting (XSS)**
   - Content Security Policy (CSP)
   - Output encoding
   - Input sanitization
   - React защита от XSS

8. **Insecure Deserialization**
   - Валидация десериализованных данных
   - Signed serialization tokens
   - Ограничение типов объектов

9. **Using Components with Known Vulnerabilities**
   - Регулярное обновление зависимостей
   - Vulnerability scanning
   - Dependency lock files
   - Security advisories monitoring

10. **Insufficient Logging & Monitoring**
    - Comprehensive audit logs
    - Real-time monitoring
    - Anomaly detection
    - Incident response procedures

### Заголовки безопасности

**Nginx конфигурация:**
```nginx
# Security headers
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;" always;

# Hide server information
server_tokens off;
```

**FastAPI Security Headers:**
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# HTTPS redirect в production
if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)
```

## Rate Limiting и DDoS защита

### Уровни ограничений

**Глобальные лимиты:**
- 100 запросов в минуту на IP
- 1000 запросов в час на IP
- 10000 запросов в день на IP

**API-специфичные лимиты:**
```python
# Парсинг новостей
"/api/news/parse": {
    "calls": 5,
    "period": 60  # секунды
}

# AI операции
"/api/news-generation/*": {
    "calls": 10,
    "period": 60
}

# Генерация изображений
"/api/images/generate": {
    "calls": 3,
    "period": 60
}

# Аутентификация
"/api/auth/login": {
    "calls": 5,
    "period": 300  # 5 минут
}
```

**Nginx rate limiting:**
```nginx
# Зоны ограничений
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=api:10m rate=2r/s;
limit_req_zone $binary_remote_addr zone=auth:10m rate=1r/m;

# Применение ограничений
location /api/auth/ {
    limit_req zone=auth burst=3 nodelay;
}

location /api/ {
    limit_req zone=api burst=5 nodelay;
}

location / {
    limit_req zone=general burst=10 nodelay;
}
```

### Fail2Ban настройка

**Jail конфигурация:**
```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
findtime = 600
bantime = 3600

[nginx-noscript]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 6
findtime = 600
bantime = 3600

[nginx-badbots]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2
findtime = 600
bantime = 86400
```

## Защита данных

### Шифрование

**В покое (at rest):**
- Пароли: bcrypt с cost=12
- Секретные ключи: переменные окружения
- Файлы бэкапов: GPG шифрование
- Логи: ротация с сжатием

**В транзите (in transit):**
- HTTPS с TLS 1.2+
- Perfect Forward Secrecy
- HSTS заголовки
- Certificate pinning (планируется)

**В памяти:**
- Очистка секретов после использования
- Secure memory allocation для ключей
- Memory dumps защита

### Управление секретами

**Структура секретов:**
```bash
# Критические секреты
JWT_SECRET_KEY=...          # 256-bit random
DATABASE_URL=...            # Connection string с паролем
OPENAI_API_KEY=...         # API ключ

# Интеграционные секреты
BITRIX_API_TOKEN=...       # Токен доступа к Bitrix
IMAGE_PROVIDER_KEY=...     # Ключ провайдера изображений

# Системные секреты
SECRET_KEY=...             # Django-style secret
BACKUP_ENCRYPTION_KEY=...  # Для шифрования бэкапов
```

**Ротация секретов:**
- JWT ключи: каждые 90 дней
- API ключи: каждые 180 дней
- Пароли БД: каждые 365 дней
- Сертификаты: автоматически через Let's Encrypt

**Хранение секретов:**
```bash
# .env файл (только для dev)
# Production: переменные окружения systemd

# /etc/systemd/system/medapp-backend.service
[Service]
Environment="JWT_SECRET_KEY=actual_secret_key"
Environment="DATABASE_URL=postgresql://..."
EnvironmentFile=/opt/medapp/secrets/.env.production

# Права доступа
chmod 600 /opt/medapp/secrets/.env.production
chown medapp:medapp /opt/medapp/secrets/.env.production
```

## Аудит и мониторинг

### Логирование событий безопасности

**Категории событий:**
1. **Аутентификация**
   - Успешные входы
   - Неудачные попытки входа
   - Выходы из системы
   - Смена паролей

2. **Авторизация**
   - Попытки доступа к запрещенным ресурсам
   - Эскалация привилегий
   - Изменения ролей

3. **Конфиденциальные операции**
   - Создание/удаление пользователей
   - Изменение настроек системы
   - Доступ к данным
   - API ключей операции

4. **Системные события**
   - Изменения конфигурации
   - Перезапуски сервисов
   - Сбои безопасности
   - Подозрительная активность

**Формат логов:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO|WARN|ERROR|CRITICAL",
  "event_type": "auth_success|auth_failed|access_denied|config_change",
  "user_id": "123",
  "username": "admin",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "resource": "/api/users",
  "action": "CREATE|READ|UPDATE|DELETE",
  "details": {
    "additional_context": "..."
  },
  "session_id": "abc123",
  "request_id": "req_456"
}
```

### Мониторинг безопасности

**Метрики для отслеживания:**
- Количество неудачных попыток входа
- Превышения rate limits
- Подозрительные паттерны доступа
- Аномальное использование API
- Географические аномалии
- Время ответа аутентификации

**Алерты:**
```python
# Примеры правил алертов
SECURITY_ALERTS = {
    "failed_logins": {
        "threshold": 5,
        "timeframe": "5m",
        "action": "block_ip"
    },
    "privilege_escalation": {
        "threshold": 1,
        "timeframe": "1s",
        "action": "immediate_alert"
    },
    "api_abuse": {
        "threshold": 100,
        "timeframe": "1m",
        "action": "rate_limit"
    }
}
```

**SIEM интеграция:**
```bash
# Отправка логов в централизованную систему
rsyslog конфигурация для отправки в ELK/Splunk

# Примеры destination
*.* @@siem-server:514
auth.* @@security-log-server:1514
```

## Управление уязвимостями

### Процесс обновления безопасности

**Критические обновления (0-day):**
1. Получение уведомления о уязвимости
2. Оценка влияния на систему
3. Экстренное планирование обновления
4. Применение патча в течение 24 часов
5. Верификация исправления
6. Документирование изменений

**Регулярные обновления:**
1. Еженедельная проверка security advisories
2. Тестирование обновлений в staging
3. Планирование maintenance window
4. Применение обновлений в production
5. Мониторинг после обновления

**Сканирование уязвимостей:**
```bash
# Автоматическое сканирование зависимостей
npm audit                    # Node.js зависимости
pip-audit                   # Python зависимости
safety check               # Python security check

# Системное сканирование
lynis audit system         # System security audit
chkrootkit                 # Rootkit detection
rkhunter --check           # Another rootkit hunter

# Web application scanning
zap-baseline.py -t https://yourdomain.com  # OWASP ZAP
nmap -sS -O yourdomain.com                 # Network scanning
```

### Vulnerability Management Program

**Классификация уязвимостей:**
- **Critical**: CVSS 9.0-10.0 - Исправление в течение 24 часов
- **High**: CVSS 7.0-8.9 - Исправление в течение 7 дней
- **Medium**: CVSS 4.0-6.9 - Исправление в течение 30 дней
- **Low**: CVSS 0.1-3.9 - Исправление в течение 90 дней

**Отслеживание:**
- CVE базы данных
- GitHub Security Advisories
- Vendor security bulletins
- Security mailing lists

## Incident Response

### Процедура реагирования на инциденты

**Фазы реагирования:**

1. **Обнаружение (Detection)**
   - Мониторинг систем безопасности
   - Анализ логов и алертов
   - Уведомления от пользователей
   - Внешние источники (threat intel)

2. **Идентификация (Identification)**
   - Классификация инцидента
   - Оценка масштаба
   - Определение затронутых систем
   - Документирование initial findings

3. **Сдерживание (Containment)**
   - Изоляция затронутых систем
   - Предотвращение распространения
   - Сохранение доказательств
   - Временные меры защиты

4. **Искоренение (Eradication)**
   - Удаление угрозы
   - Устранение уязвимостей
   - Обновление безопасности
   - Патчинг системы

5. **Восстановление (Recovery)**
   - Восстановление сервисов
   - Мониторинг активности
   - Валидация безопасности
   - Возврат к нормальной работе

6. **Извлечение уроков (Lessons Learned)**
   - Post-incident анализ
   - Обновление процедур
   - Улучшение защиты
   - Документирование

**Классификация инцидентов:**

**Severity 1 (Critical):**
- Компрометация административных аккаунтов
- Утечка данных пользователей
- Полная недоступность системы
- Активная атака в реальном времени

**Severity 2 (High):**
- Компрометация пользовательских аккаунтов
- Несанкционированное изменение данных
- Частичная недоступность системы
- Подозрительная активность

**Severity 3 (Medium):**
- Попытки взлома
- Аномальная сетевая активность
- Нарушения политик безопасности
- Потенциальные уязвимости

**Severity 4 (Low):**
- Информационные события
- Незначительные нарушения
- Ложные срабатывания
- Профилактические уведомления

### Контакты экстренного реагирования

```bash
# Security Team
Primary:   security@company.com
Phone:     +7-xxx-xxx-xxxx

# System Administrators
Primary:   ops@company.com
Phone:     +7-xxx-xxx-xxxx

# Management
CTO:       cto@company.com
Phone:     +7-xxx-xxx-xxxx

# External Resources
Security Consultant: consultant@security-firm.com
Legal:              legal@company.com
PR:                 pr@company.com
```

## Compliance и политики

### Регуляторные требования

**GDPR (если применимо):**
- Право на забвение (данные пользователей)
- Согласие на обработку
- Уведомление о нарушениях (72 часа)
- Data Protection Officer

**Российское законодательство:**
- ФЗ "О персональных данных"
- Требования к локализации данных
- Уведомление Роскомнадзора
- Аудит безопасности

**Отраслевые стандарты:**
- ISO 27001 - Управление информационной безопасностью
- NIST Cybersecurity Framework
- OWASP Application Security

### Политики доступа

**Принципы:**
- Least Privilege - минимальные необходимые права
- Need to Know - доступ только к необходимой информации
- Separation of Duties - разделение критических функций
- Regular Review - регулярный пересмотр доступа

**Жизненный цикл доступа:**
1. **Предоставление доступа**
   - Официальный запрос
   - Одобрение руководителя
   - Конфигурация прав
   - Документирование

2. **Изменение доступа**
   - Запрос на изменение
   - Обоснование необходимости
   - Одобрение изменений
   - Реконфигурация

3. **Отзыв доступа**
   - Увольнение сотрудника
   - Смена роли
   - Истечение срока
   - Немедленная блокировка

**Регулярный аудит доступа:**
```bash
# Скрипт аудита доступа
#!/bin/bash
# access_audit.sh

echo "=== Access Audit Report $(date) ==="

# Проверка активных пользователей
echo "Active users in system:"
psql medapp_db -c "
SELECT username, role, project, created_at,
       CASE WHEN created_at < NOW() - INTERVAL '90 days'
            THEN 'REVIEW_REQUIRED'
            ELSE 'OK'
       END as status
FROM users
ORDER BY created_at DESC;
"

# Проверка последней активности
echo -e "\nUser activity (last 30 days):"
grep "auth_success" /var/log/medapp/security.log | \
awk '{print $3}' | sort | uniq -c | sort -nr

# Проверка привилегированных аккаунтов
echo -e "\nPrivileged accounts:"
psql medapp_db -c "
SELECT username, role, created_at
FROM users
WHERE role = 'admin'
ORDER BY created_at;
"
```

## Резервное копирование и восстановление

### Стратегия бэкапов

**Типы бэкапов:**
1. **Ежедневные** - инкрементальные БД + конфигурации
2. **Еженедельные** - полные бэкапы системы
3. **Ежемесячные** - архивные копии для долгосрочного хранения

**Шифрование бэкапов:**
```bash
# Бэкап с шифрованием
pg_dump medapp_db | gzip | gpg --symmetric --cipher-algo AES256 --output backup_$(date +%Y%m%d).sql.gz.gpg

# Восстановление
gpg --decrypt backup_20240115.sql.gz.gpg | gunzip | psql medapp_db
```

**Тестирование восстановления:**
- Ежемесячные тесты восстановления
- Проверка целостности данных
- Валидация процедур DR
- Документирование результатов

### Business Continuity Plan

**RTO/RPO цели:**
- **RTO (Recovery Time Objective)**: 4 часа
- **RPO (Recovery Point Objective)**: 1 час

**Критичность компонентов:**
1. **Tier 1 (Critical)**: База данных, API Backend
2. **Tier 2 (Important)**: Frontend, Image Storage
3. **Tier 3 (Standard)**: Monitoring, Logs

**Процедуры аварийного восстановления:**
1. Оценка масштаба инцидента
2. Активация emergency response team
3. Изоляция поврежденных компонентов
4. Восстановление из бэкапов
5. Тестирование функциональности
6. Возобновление сервиса
7. Post-mortem анализ

Этот документ должен регулярно пересматриваться и обновляться в соответствии с изменениями в угрозах безопасности и технологиях.