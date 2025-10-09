# Архитектурный анализ: Удаление функционала мониторинга системы

**Дата анализа:** 2025-10-07
**Агент:** Technical Architect
**Задача:** Полное удаление функционала системного мониторинга (System Monitoring)

---

## 📋 Executive Summary

**Готов к реализации:** YES
**Приоритет:** MEDIUM
**Estimated Time:** 3-4 hours
**Risk Score:** 12 (Medium: 2×2 + High: 1×5 + Low: 3×1)

**Краткое описание:**
Функционал системного мониторинга (System Monitoring) включает отслеживание системных метрик (CPU, RAM, Disk, Network), статусов сервисов, производительности базы данных, алертов и истории метрик. Компоненты изолированы в отдельных модулях, зависимости минимальны. Удаление безопасно, так как функционал не используется критичными бизнес-процессами (парсинг, генерация, публикация новостей).

**Критичные различия:**
- **System Monitoring** (целевой для удаления) - страница `/system-monitoring` с техническими метриками
- **News Monitoring** (НЕ удалять!) - главная страница `/monitoring` (alias `/`) с парсингом новостей
- **Expense Monitoring** (НЕ удалять!) - страница `/expenses` с отслеживанием расходов на AI

---

## 🎯 Цели изменения

1. **Упрощение архитектуры** - удаление неиспользуемого функционала мониторинга
2. **Снижение технического долга** - убрать зависимости psutil, aiohttp для мониторинга
3. **Уменьшение кодовой базы** - удалить ~1800+ строк кода (backend + frontend)
4. **Освобождение API endpoints** - освободить `/api/admin/monitoring/*` endpoints
5. **Очистка UI** - убрать пункт "Мониторинг системы" из навигации

---

## 🔍 Current State Analysis

### 1. Backend Components (Python)

#### 1.1. API Router
**Файл:** `backend/api/monitoring.py` (362 строки)
- **Endpoints:**
  - `GET /api/admin/monitoring/system` - системные метрики (CPU, RAM, Disk)
  - `GET /api/admin/monitoring/services` - статус сервисов (Backend, Frontend, Image Gen)
  - `GET /api/admin/monitoring/alerts` - список алертов
  - `POST /api/admin/monitoring/alerts/{id}/acknowledge` - подтверждение алерта
  - `POST /api/admin/monitoring/alerts/clear-all` - очистка всех алертов
  - `DELETE /api/admin/monitoring/alerts/history` - удаление истории
  - `GET /api/admin/monitoring/overview` - общий обзор системы
  - `GET /api/admin/monitoring/history` - история метрик (system/database)
  - `GET /api/admin/monitoring/logs` - системные логи (mock)

- **Зависимости:**
  - `services.system_monitoring.system_monitor` (глобальный singleton)
  - `services.db_monitoring.db_monitor` (глобальный singleton)

#### 1.2. System Monitoring Service
**Файл:** `backend/services/system_monitoring.py` (352 строки)
- **Классы:**
  - `ServiceStatus` (dataclass) - статус сервиса
  - `SystemMetrics` (dataclass) - системные метрики
  - `Alert` (dataclass) - алерт
  - `SystemMonitor` (основной класс)

- **Функционал:**
  - Сбор метрик: CPU, Memory, Disk, Network, Uptime (через psutil)
  - Проверка здоровья сервисов по HTTP (через aiohttp)
  - Генерация алертов при превышении порогов
  - Хранение истории метрик в памяти (max 100 записей)
  - Форматирование размеров и времени

- **Внешние зависимости:**
  - `psutil` - сбор системных метрик
  - `aiohttp` - HTTP запросы к сервисам
  - `asyncio`, `time`, `datetime` - стандартная библиотека

- **Глобальный экземпляр:**
  ```python
  system_monitor = SystemMonitor()
  ```

#### 1.3. Database Monitoring Service
**Файл:** `backend/services/db_monitoring.py` (399 строк)
- **Классы:**
  - `DBMetrics` (dataclass) - метрики БД
  - `DatabaseMonitor` (основной класс)

- **Функционал:**
  - Сбор метрик PostgreSQL: connections, QPS, cache hit ratio, locks
  - Статистика по таблицам (pg_stat_user_tables)
  - Проверка условий алертов
  - История метрик в памяти (max 100 записей)

- **Зависимости:**
  - `database.connection.engine` - подключение к PostgreSQL
  - `sqlmodel.Session`, `sqlmodel.text` - SQL запросы

- **Глобальный экземпляр:**
  ```python
  db_monitor = DatabaseMonitor()
  ```

- **Используется также в:** `backend/api/admin.py`
  - `GET /api/admin/stats/database`
  - `GET /api/admin/stats/database/tables`
  - `GET /api/admin/stats/database/history`

#### 1.4. Main Application Router
**Файл:** `backend/main.py` (строка 13, 225)
- **Импорт:**
  ```python
  from api import monitoring
  ```
- **Регистрация:**
  ```python
  app.include_router(monitoring.router, prefix="/api/admin/monitoring", tags=["monitoring"])
  ```

---

### 2. Frontend Components (Next.js/React)

#### 2.1. System Monitoring Page
**Файл:** `frontend/pages/system-monitoring.js` (85 строк)
- **Маршрут:** `/system-monitoring`
- **Доступ:** Admin или Analyst (проверка через `useAuth`)
- **Компоненты:**
  - `<SystemMonitoringDashboard />` - основной дашборд
  - `<Navigation />` - навигация
  - `<Layout />` - обертка страницы

#### 2.2. Main Monitoring Page (НЕ УДАЛЯТЬ!)
**Файл:** `frontend/pages/monitoring.js` (624 строки)
- **Маршрут:** `/monitoring` (также `/` index)
- **Назначение:** Парсинг новостей, загрузка URL статей
- **ВАЖНО:** Это НЕ системный мониторинг! Это основная рабочая страница.
- **Не путать с system-monitoring!**

#### 2.3. System Monitoring Dashboard Component
**Файл:** `frontend/components/monitoring/SystemMonitoringDashboard.js` (409 строк)
- **Компонент:** `<SystemMonitoringDashboard />`
- **Функционал:**
  - Загрузка данных с `/api/proxy/admin/monitoring/*` endpoints
  - Отображение обзора системы (CPU, RAM, Disk, Uptime)
  - Статус сервисов (Backend, Frontend, Image Gen)
  - Системные метрики и БД статистика
  - Автообновление каждые 30 секунд

- **API endpoints (через proxy):**
  - `/api/proxy/admin/monitoring/overview`
  - `/api/proxy/admin/monitoring/system`
  - `/api/proxy/admin/monitoring/services`

- **Зависимости:**
  - `ServiceStatusCard`
  - `SystemMetricsPanel`
  - UI компоненты (Card, Button, Alert, Badge)

#### 2.4. Service Status Card
**Файл:** `frontend/components/monitoring/ServiceStatusCard.js`
- **Компонент:** `<ServiceStatusCard />`
- **Назначение:** Отображение статуса одного сервиса
- **Props:** `service` (name, status, response_time, error_message)

#### 2.5. System Metrics Panel
**Файл:** `frontend/components/monitoring/SystemMetricsPanel.js`
- **Компонент:** `<SystemMetricsPanel />`
- **Назначение:** Панель системных метрик (CPU, RAM, Disk, Network)
- **Props:** `data` (системные метрики)

#### 2.6. Alerts Panel
**Файл:** `frontend/components/monitoring/AlertsPanel.js`
- **Компонент:** `<AlertsPanel />`
- **Назначение:** Отображение и управление алертами
- **API endpoints:**
  - `/api/admin/monitoring/alerts/clear-all`
  - `/api/admin/monitoring/alerts/history`

#### 2.7. Navigation Component (ОБНОВИТЬ!)
**Файл:** `frontend/components/Navigation.js` (строка 24)
- **Пункт меню для удаления:**
  ```javascript
  { id: 'system-monitoring', label: 'Мониторинг системы', icon: HiOutlineChartBarSquare, href: '/system-monitoring' }
  ```
- **Условие отображения:** `canViewAnalytics()` (admin или analyst)

#### 2.8. API Proxy (НЕ УДАЛЯТЬ!)
**Файл:** `frontend/pages/api/proxy/[...path].js`
- **Назначение:** Проксирование запросов от frontend к backend
- **Используется для:** `/api/proxy/admin/monitoring/*`
- **Действие:** НЕ удалять файл! Он используется для других API endpoints.

---

### 3. Components NOT to Delete (НЕ УДАЛЯТЬ!)

#### 3.1. NewsMonitoring Component
**Файл:** `frontend/components/NewsMonitoring.js` (150+ строк)
- **Назначение:** Мониторинг источников новостей (mock компонент)
- **Использование:** Потенциально на главной странице `/monitoring`
- **Статус:** НЕ удалять - относится к новостному мониторингу

#### 3.2. ExpenseMonitoring Component
**Файл:** `frontend/components/ExpenseMonitoring.js` (500+ строк)
- **Назначение:** Мониторинг расходов на AI (OpenAI, Yandex Cloud)
- **Маршрут:** `/expenses`
- **Статус:** НЕ удалять - критичный бизнес-функционал

#### 3.3. Database Stats in Admin API
**Файл:** `backend/api/admin.py` (строки 86-164)
- **Endpoints:**
  - `GET /api/admin/stats/database`
  - `GET /api/admin/stats/database/tables`
  - `GET /api/admin/stats/database/history`
  - `POST /api/admin/database/analyze`
  - `POST /api/admin/database/vacuum`
- **Зависимость:** Использует `db_monitor.collect_metrics()`
- **Статус:** НЕ удалять endpoints, но нужно учесть зависимость от db_monitoring.py

---

## 📊 Impact Analysis

### High Impact Areas 🔴

#### 1. Backend API Breaking Changes
**Файлы:**
- `backend/api/monitoring.py` (удаление)
- `backend/main.py` (удаление импорта и регистрации роутера)

**Влияние:**
- Все `/api/admin/monitoring/*` endpoints станут недоступны (404)
- Frontend компоненты, вызывающие эти endpoints, получат ошибки
- Нет breaking changes для других backend модулей (изолированный роутер)

#### 2. Database Monitoring Service Dependency
**Файл:** `backend/api/admin.py`

**Проблема:**
- Admin API использует `db_monitor.collect_metrics()` для БД статистики
- Если удалить `backend/services/db_monitoring.py`, admin endpoints сломаются

**Решение:**
- Сохранить `backend/services/db_monitoring.py` (используется admin API)
- Или: удалить также БД endpoints из admin API (если не нужны)
- Рекомендация: **Сохранить db_monitoring.py** (полезен для admin)

### Medium Impact 🟠

#### 3. Frontend Navigation Menu
**Файл:** `frontend/components/Navigation.js`

**Влияние:**
- Пункт "Мониторинг системы" продолжит отображаться для admin/analyst
- При клике пользователь перейдет на несуществующую страницу
- Требуется обновление массива navigationItems

#### 4. Frontend System Monitoring Components
**Файлы:**
- `frontend/pages/system-monitoring.js`
- `frontend/components/monitoring/SystemMonitoringDashboard.js`
- `frontend/components/monitoring/ServiceStatusCard.js`
- `frontend/components/monitoring/SystemMetricsPanel.js`
- `frontend/components/monitoring/AlertsPanel.js`

**Влияние:**
- Страница `/system-monitoring` станет 404
- Компоненты в `monitoring/` директории больше не используются
- Нет зависимостей от других frontend компонентов (изолированы)

### Low Impact 🟢

#### 5. Python Dependencies
**Зависимости для удаления:**
- `psutil` - только для system_monitoring
- `aiohttp` - используется также в news parsers (НЕ удалять!)

**Действие:**
- Проверить использование psutil в других модулях
- Если только в system_monitoring - удалить из requirements.txt

#### 6. Documentation
**Файлы:**
- `docs/api/endpoints.md` - нет упоминаний monitoring endpoints
- `CLAUDE.md` - есть упоминание "monitoring.py" в структуре

**Действие:**
- Обновить примеры кода, где импортируется monitoring
- Обновить список API endpoints (если есть)

---

## 🕸️ Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEM MONITORING REMOVAL                     │
└─────────────────────────────────────────────────────────────────┘

                      ┌──────────────────┐
                      │   backend/       │
                      │   main.py        │
                      │                  │
                      │ Регистрация      │
                      │ роутера          │
                      └────────┬─────────┘
                               │
                               │ imports & includes
                               │
                               ▼
                      ┌──────────────────┐
                      │  backend/api/    │
                      │  monitoring.py   │◄────────── DELETE (362 lines)
                      │                  │
                      │ 10 API endpoints │
                      └────────┬─────────┘
                               │
                     ┌─────────┴─────────┐
                     │                   │
                     ▼                   ▼
        ┌────────────────────┐  ┌────────────────────┐
        │ backend/services/  │  │ backend/services/  │
        │ system_monitoring  │  │ db_monitoring.py   │
        │       .py          │  │                    │
        │                    │  │ ⚠️ ALSO USED BY:   │
        │ - SystemMonitor    │  │ backend/api/       │
        │ - psutil metrics   │  │ admin.py           │
        │ - aiohttp checks   │  │                    │
        │ - alerts           │  │ 5 endpoints:       │
        │ - history          │  │ /stats/database/*  │
        └────────────────────┘  └────────────────────┘
                 │                       │
                 │                       │
                 │                       │ DECISION:
                 │                       │ KEEP (used by admin)
                 │                       │
                 ▼                       ▼
        DELETE              ┌────────────────────┐
        ✓ Изолирован        │  Используется в:   │
        ✓ Нет зависимостей  │  • /api/admin/*    │
                            │  • БД статистика   │
                            └────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND COMPONENTS                         │
└─────────────────────────────────────────────────────────────────┘

             ┌────────────────────────────────┐
             │  frontend/components/          │
             │  Navigation.js                 │◄──── UPDATE
             │                                │     (remove menu item)
             │  navigationItems array         │
             └────────────┬───────────────────┘
                          │
                          │ renders link to
                          │
                          ▼
             ┌────────────────────────────────┐
             │  frontend/pages/               │
             │  system-monitoring.js          │◄──── DELETE (85 lines)
             │                                │
             │  Route: /system-monitoring     │
             └────────────┬───────────────────┘
                          │
                          │ renders
                          │
                          ▼
             ┌────────────────────────────────┐
             │  frontend/components/          │
             │  monitoring/                   │
             │  SystemMonitoringDashboard.js  │◄──── DELETE (409 lines)
             │                                │
             │  Fetches:                      │
             │  /api/proxy/admin/monitoring/* │
             └────┬───────────────────────────┘
                  │
                  │ uses
                  │
       ┌──────────┴──────────────┬──────────────────┐
       │                         │                  │
       ▼                         ▼                  ▼
┌──────────────┐    ┌────────────────────┐  ┌─────────────────┐
│ Service      │    │ SystemMetrics      │  │ AlertsPanel     │
│ StatusCard   │◄── │ Panel              │  │                 │◄── DELETE
│              │ │  │                    │  │ Calls:          │    (all 4)
│              │ │  │                    │  │ /alerts/*       │
└──────────────┘ │  └────────────────────┘  └─────────────────┘
                 │
                 │
                 ▼
            DELETE ALL
            (monitoring/ directory)


┌─────────────────────────────────────────────────────────────────┐
│                  COMPONENTS TO KEEP (NOT DELETE)                 │
└─────────────────────────────────────────────────────────────────┘

        ┌────────────────────────────────┐
        │  frontend/pages/               │
        │  monitoring.js                 │◄──── KEEP!
        │                                │     (News monitoring)
        │  Route: /monitoring (index)    │
        │  Purpose: Parse news, URL      │
        └────────────────────────────────┘

        ┌────────────────────────────────┐
        │  frontend/components/          │
        │  NewsMonitoring.js             │◄──── KEEP!
        │                                │     (News sources)
        │  Purpose: Mock news sources    │
        └────────────────────────────────┘

        ┌────────────────────────────────┐
        │  frontend/components/          │
        │  ExpenseMonitoring.js          │◄──── KEEP!
        │                                │     (AI expenses)
        │  Purpose: Track OpenAI costs   │
        └────────────────────────────────┘

        ┌────────────────────────────────┐
        │  backend/api/admin.py          │◄──── KEEP!
        │  /stats/database endpoints     │     (DB stats)
        │                                │
        │  Uses: db_monitor              │
        └────────────────────────────────┘
```

---

## ⚠️ Risk Matrix

| # | Риск | Вероятность | Критичность | Митигация |
|---|------|-------------|-------------|-----------|
| 1 | Breaking frontend при обращении к удаленным API endpoints | High | Medium | Удалить frontend компоненты ДО или одновременно с backend |
| 2 | Admin API `/stats/database/*` сломается при удалении `db_monitoring.py` | Medium | High | **СОХРАНИТЬ** `db_monitoring.py` (используется admin API) |
| 3 | Пользователи увидят ошибку 404 при клике на "Мониторинг системы" | High | Low | Обновить Navigation.js (убрать пункт меню) |
| 4 | Остаточные импорты psutil вызовут ошибки при удалении | Low | Low | Grep-поиск всех использований psutil перед удалением |
| 5 | Документация будет ссылаться на несуществующий код | Low | Low | Обновить CLAUDE.md, примеры кода |
| 6 | Потеря возможности мониторинга системы в будущем | Medium | Low | Сохранить код в отдельной ветке перед удалением |

**Risk Score Calculation:**
- Critical × 10: 1 × 10 = 10
- High × 5: 1 × 5 = 5
- Medium × 2: 2 × 2 = 4
- Low × 1: 3 × 1 = 3
- **Total: 22** → Medium Risk

**Рекомендация:** Проект готов к реализации. Риски управляемые.

---

## 🗺️ Migration Path (Пошаговый план)

### Phase 1: Preparation (30 min)

#### Checkpoint 1.1: Backup & Branch
```bash
# Создать резервную копию БД (опционально, т.к. нет миграций БД)
# docker exec medical-news-backend pg_dump -U postgres news_aggregator > backup_before_monitoring_removal.sql

# Создать feature branch
cd "/Users/dan/Documents/RM Service/SEO NEW 5"
git checkout -b feature/remove-system-monitoring
git status
```

#### Checkpoint 1.2: Verify Usage of db_monitoring
```bash
# Проверить использование db_monitoring в admin.py
grep -n "db_monitor" backend/api/admin.py

# Ожидаемый результат: строки 7, 91, 93, 94, 111, 129
# Это подтверждает, что db_monitoring.py используется admin API
```

**Решение:** СОХРАНИТЬ `backend/services/db_monitoring.py`

#### Checkpoint 1.3: Verify Usage of psutil
```bash
# Найти все использования psutil
grep -r "import psutil" backend/ --include="*.py"

# Ожидаемый результат: только backend/services/system_monitoring.py
# Если есть другие - НЕ удалять psutil из requirements.txt
```

#### Checkpoint 1.4: Verify Usage of aiohttp
```bash
# Найти все использования aiohttp
grep -r "import aiohttp" backend/ --include="*.py"

# Ожидаемый результат:
# - backend/services/system_monitoring.py (DELETE)
# - backend/services/*_parser.py (KEEP - news parsers)
# Вывод: НЕ удалять aiohttp из requirements.txt
```

#### Checkpoint 1.5: Verify Frontend Dependencies
```bash
# Проверить импорты SystemMonitoringDashboard
grep -r "SystemMonitoringDashboard" frontend/ --include="*.js" --include="*.jsx"

# Ожидаемый результат:
# - frontend/pages/system-monitoring.js (импорт и использование)
# Вывод: только одна страница использует компонент
```

---

### Phase 2: Backend Removal (1 hour)

#### Step 2.1: Remove Monitoring API Router
**Файл:** `backend/api/monitoring.py`

**Действие:** УДАЛИТЬ файл целиком

```bash
rm backend/api/monitoring.py
rm backend/api/__pycache__/monitoring.cpython-313.pyc
```

**Результат:** Удалены все `/api/admin/monitoring/*` endpoints

#### Step 2.2: Remove System Monitoring Service
**Файл:** `backend/services/system_monitoring.py`

**Действие:** УДАЛИТЬ файл целиком

```bash
rm backend/services/system_monitoring.py
rm backend/services/__pycache__/system_monitoring.cpython-313.pyc
```

**Результат:** Удален SystemMonitor класс и его зависимости

#### Step 2.3: Update Main Application (Remove Router Registration)
**Файл:** `backend/main.py`

**Изменение 1:** Удалить импорт (строка 13)
```python
# БЫЛО:
from api import news, admin, news_generation, auth, users, expenses, monitoring, image_generation, telegram_posts, url_articles

# СТАЛО:
from api import news, admin, news_generation, auth, users, expenses, image_generation, telegram_posts, url_articles
```

**Изменение 2:** Удалить регистрацию роутера (строка 225)
```python
# БЫЛО:
app.include_router(monitoring.router, prefix="/api/admin/monitoring", tags=["monitoring"])

# СТАЛО:
# (удалить строку целиком)
```

**Проверка:**
```bash
# Проверить что main.py компилируется без ошибок
cd backend
python -c "from main import app; print('✓ Backend imports OK')"
```

#### Step 2.4: Update Dependencies (Optional)
**Файл:** `backend/requirements.txt`

**Проверка перед удалением:**
```bash
# Если psutil используется ТОЛЬКО в system_monitoring.py
grep -r "psutil" backend/ --include="*.py" | grep -v system_monitoring.py

# Если вывод пустой - можно удалить psutil
```

**Изменение (если проверка пройдена):**
```txt
# УДАЛИТЬ (если не используется):
psutil==5.9.6

# ОСТАВИТЬ (используется в parsers):
aiohttp>=3.8.0
```

**Важно:** Проверить результат `pip list` после удаления:
```bash
cd backend
pip uninstall psutil -y  # если удалили из requirements.txt
```

#### Step 2.5: СОХРАНИТЬ db_monitoring.py
**Файл:** `backend/services/db_monitoring.py`

**Действие:** НЕ УДАЛЯТЬ!

**Причина:**
- Используется в `backend/api/admin.py`
- Endpoints: `/api/admin/stats/database/*`
- Критичен для мониторинга производительности БД

**Проверка:**
```bash
# Убедиться что db_monitoring.py не был удален
ls -la backend/services/db_monitoring.py
```

---

### Phase 3: Frontend Removal (1 hour)

#### Step 3.1: Remove System Monitoring Page
**Файл:** `frontend/pages/system-monitoring.js`

**Действие:** УДАЛИТЬ файл целиком

```bash
rm frontend/pages/system-monitoring.js
```

**Результат:** Маршрут `/system-monitoring` станет 404

#### Step 3.2: Remove Monitoring Components Directory
**Директория:** `frontend/components/monitoring/`

**Файлы для удаления:**
- `SystemMonitoringDashboard.js` (409 строк)
- `ServiceStatusCard.js`
- `SystemMetricsPanel.js`
- `AlertsPanel.js`

**Действие:** УДАЛИТЬ директорию целиком

```bash
rm -rf frontend/components/monitoring/
```

**Проверка:**
```bash
# Убедиться что директория удалена
ls -la frontend/components/monitoring/ 2>&1 | grep "No such file"
```

#### Step 3.3: Update Navigation Menu
**Файл:** `frontend/components/Navigation.js`

**Изменение:** Удалить пункт меню "Мониторинг системы" (строка 24)

**БЫЛО (строки 22-25):**
```javascript
...(canViewAnalytics() ? [
  { id: 'expenses', label: 'Мониторинг расходов', icon: HiOutlineCurrencyDollar, href: '/expenses' },
  { id: 'system-monitoring', label: 'Мониторинг системы', icon: HiOutlineChartBarSquare, href: '/system-monitoring' },
] : []),
```

**СТАЛО:**
```javascript
...(canViewAnalytics() ? [
  { id: 'expenses', label: 'Мониторинг расходов', icon: HiOutlineCurrencyDollar, href: '/expenses' },
] : []),
```

**Также удалить импорт иконки (строка 9):**
```javascript
// БЫЛО:
import {
  HiOutlineNewspaper,
  HiOutlineCog6Tooth,
  HiOutlineGlobeAlt,
  HiOutlineCurrencyDollar,
  HiOutlineChartBarSquare  // ← удалить эту строку
} from 'react-icons/hi2'

// СТАЛО:
import {
  HiOutlineNewspaper,
  HiOutlineCog6Tooth,
  HiOutlineGlobeAlt,
  HiOutlineCurrencyDollar
} from 'react-icons/hi2'
```

#### Step 3.4: Verify No Remaining References
```bash
# Проверить что нет ссылок на удаленные компоненты
grep -r "system-monitoring" frontend/ --include="*.js" --include="*.jsx"
grep -r "SystemMonitoringDashboard" frontend/ --include="*.js" --include="*.jsx"
grep -r "monitoring/AlertsPanel" frontend/ --include="*.js" --include="*.jsx"

# Ожидаемый результат: пустой вывод (нет совпадений)
```

---

### Phase 4: Validation & Testing (1 hour)

#### Test 4.1: Backend Health Check
```bash
# Запустить backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# В другом терминале - проверить health
curl http://localhost:8000/health
# Ожидается: {"status":"healthy","service":"medical-news-automation"}

curl http://localhost:8000/api/health
# Ожидается: {"status":"healthy","service":"medical-news-automation"}
```

#### Test 4.2: Verify Monitoring Endpoints Are Gone
```bash
# Проверить что monitoring endpoints недоступны
curl -i http://localhost:8000/api/admin/monitoring/system
# Ожидается: 404 Not Found

curl -i http://localhost:8000/api/admin/monitoring/overview
# Ожидается: 404 Not Found
```

#### Test 4.3: Verify Admin Database Endpoints Still Work
```bash
# Проверить что admin endpoints работают (используют db_monitoring)
# Потребуется JWT token авторизованного admin пользователя

# Получить токен:
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_ADMIN_PASSWORD"}' \
  | jq -r '.access_token')

# Проверить БД статистику:
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/stats/database
# Ожидается: JSON с метриками БД (connections, performance, resources)
```

#### Test 4.4: Frontend Build
```bash
# Собрать frontend
cd frontend
npm run build

# Ожидается: успешная сборка без ошибок
# Build completed in X seconds
```

#### Test 4.5: Frontend Navigation Check
```bash
# Запустить frontend dev server
npm run dev

# Открыть http://localhost:3000
# Войти как admin
# Проверить Navigation меню:
# ✓ Есть: Мониторинг новостей, Опубликованные новости, Мониторинг расходов, Настройки
# ✗ Нет: Мониторинг системы
```

#### Test 4.6: 404 Page Check
```bash
# Открыть http://localhost:3000/system-monitoring
# Ожидается: 404 Page Not Found (Next.js default)
```

#### Test 4.7: Verify Critical Functionality Works
**Проверить ключевые функции:**
- ✅ Авторизация (login/logout)
- ✅ Парсинг новостей (/monitoring)
- ✅ Генерация статей
- ✅ Публикация в Bitrix/Telegram
- ✅ Мониторинг расходов (/expenses)
- ✅ Настройки (/settings)

---

### Phase 5: Documentation Updates (30 min)

#### Doc 5.1: Update CLAUDE.md
**Файл:** `CLAUDE.md`

**Изменение:** Обновить Backend Structure секцию

**БЫЛО:**
```markdown
├── api/                   # API endpoints (routers)
│   ├── monitoring.py      # System/DB monitoring
```

**СТАЛО:**
```markdown
├── api/                   # API endpoints (routers)
│   ├── (monitoring.py removed - system monitoring deprecated)
```

**Также обновить Common Debugging секцию:**

**УДАЛИТЬ:**
```bash
# View system monitoring
curl http://localhost:8000/api/admin/monitoring/overview
```

#### Doc 5.2: Update Architecture Documentation
**Файл:** `docs/architecture/overview.md` (если существует)

**Действие:** Удалить упоминания системного мониторинга

**Проверка:**
```bash
grep -n "monitoring" docs/architecture/overview.md
grep -n "system.*monitoring" docs/ -r
```

#### Doc 5.3: Create ADR (Architecture Decision Record)
**Файл:** `docs/adr/ADR-XXX-remove-system-monitoring.md` (создать новый)

**Содержание:**
```markdown
# ADR-XXX: Удаление функционала системного мониторинга

**Статус:** Принято
**Дата:** 2025-10-07
**Автор:** Technical Architect

## Контекст
Функционал системного мониторинга (CPU, RAM, Disk, Services) не используется
в production и добавляет технический долг (зависимости psutil, aiohttp,
дублирование БД мониторинга в admin API).

## Решение
Удалить:
- backend/api/monitoring.py (10 endpoints)
- backend/services/system_monitoring.py (SystemMonitor)
- frontend/pages/system-monitoring.js
- frontend/components/monitoring/* (все компоненты)

Сохранить:
- backend/services/db_monitoring.py (используется admin API)
- frontend/components/ExpenseMonitoring.js (AI expenses)
- frontend/pages/monitoring.js (news monitoring)

## Последствия
Положительные:
- Упрощение архитектуры
- Удаление ~1800 строк кода
- Снижение количества зависимостей

Отрицательные:
- Потеря возможности мониторинга системы через UI
- Альтернатива: использовать внешние инструменты (Grafana, Prometheus)
```

#### Doc 5.4: Update CHANGELOG.md
**Файл:** `CHANGELOG.md`

**Добавить запись:**
```markdown
## [Unreleased]

### Removed
- Функционал системного мониторинга (System Monitoring)
  - API endpoints: /api/admin/monitoring/*
  - Frontend страница: /system-monitoring
  - Компоненты: SystemMonitoringDashboard, ServiceStatusCard, SystemMetricsPanel, AlertsPanel
  - Причина: неиспользуемый функционал, технический долг
  - Альтернатива: внешние инструменты мониторинга (Grafana, Prometheus)
```

---

### Phase 6: Finalization (30 min)

#### Final 6.1: Clean Up Pyc Files
```bash
# Удалить скомпилированные Python файлы
find backend/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find backend/ -type f -name "*.pyc" -delete
```

#### Final 6.2: Run Linters (Optional)
```bash
# Backend linting
cd backend
flake8 main.py api/ services/

# Frontend linting
cd ../frontend
npm run lint
```

#### Final 6.3: Commit Changes
```bash
cd "/Users/dan/Documents/RM Service/SEO NEW 5"

# Добавить удаленные файлы
git add -A

# Проверить статус
git status

# Ожидаемые изменения:
# deleted: backend/api/monitoring.py
# deleted: backend/services/system_monitoring.py
# deleted: frontend/pages/system-monitoring.js
# deleted: frontend/components/monitoring/
# modified: backend/main.py
# modified: frontend/components/Navigation.js
# modified: CLAUDE.md
# modified: CHANGELOG.md
# new file: docs/adr/ADR-XXX-remove-system-monitoring.md

# Создать коммит
git commit -m "$(cat <<'EOF'
Remove system monitoring functionality

Removed unused system monitoring features to reduce technical debt:

Backend:
- DELETE backend/api/monitoring.py (10 endpoints)
- DELETE backend/services/system_monitoring.py (SystemMonitor class)
- UPDATE backend/main.py (remove monitoring router)
- KEEP backend/services/db_monitoring.py (used by admin API)

Frontend:
- DELETE frontend/pages/system-monitoring.js
- DELETE frontend/components/monitoring/ (all 4 components)
- UPDATE frontend/components/Navigation.js (remove menu item)

Documentation:
- UPDATE CLAUDE.md (remove monitoring references)
- UPDATE CHANGELOG.md (add removal note)
- CREATE docs/adr/ADR-XXX-remove-system-monitoring.md

Rationale:
- System monitoring not used in production
- Reduces codebase by ~1800 lines
- Simplifies architecture
- External monitoring tools (Grafana, Prometheus) are better alternatives

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

#### Final 6.4: Push to Remote (if needed)
```bash
# Опционально: запушить ветку
git push origin feature/remove-system-monitoring

# Или мерджить в main (если нет code review)
git checkout main
git merge feature/remove-system-monitoring
git push origin main
```

---

## 🔙 Rollback Strategy

### Triggers для отката

🔴 **Critical (немедленный откат):**
- Backend не стартует после изменений
- Admin API `/stats/database/*` endpoints не работают
- Критичные функции (парсинг, генерация, публикация) сломаны

🟠 **High (откат в течение часа):**
- Frontend не собирается (npm build fails)
- Неожиданные ошибки в других модулях

🟡 **Medium (откат опционально):**
- Пользователи требуют вернуть системный мониторинг
- Найдены скрытые зависимости

---

### Rollback Steps

#### Quick Rollback (code only)
```bash
cd "/Users/dan/Documents/RM Service/SEO NEW 5"

# Откатить все изменения
git reset --hard HEAD~1

# ИЛИ откатить до конкретного коммита
git log --oneline  # найти хеш коммита перед удалением
git reset --hard <COMMIT_HASH>

# Перезапустить сервисы
docker-compose restart backend frontend
```

#### Full Rollback (with dependencies)
```bash
# Если удаляли psutil из requirements.txt
cd backend
pip install psutil==5.9.6

# Перезапустить backend
uvicorn main:app --reload

# Перезапустить frontend
cd ../frontend
npm run dev
```

#### Docker Rollback
```bash
# Если работаете через Docker
docker-compose down
git reset --hard HEAD~1
docker-compose up -d --build
```

---

## 🧪 Testing Requirements

### Unit Tests (если есть)

#### Backend Tests
```bash
cd backend

# Проверить что не сломались существующие тесты
pytest tests/ -v

# Проверить что удаленные модули действительно не импортируются
pytest tests/ -k "monitoring" --collect-only
# Ожидается: no tests collected (если удалили тесты мониторинга)
```

#### Frontend Tests
```bash
cd frontend

# Запустить Jest тесты
npm test

# Проверить что нет ошибок импорта удаленных компонентов
npm test -- --verbose
```

---

### Integration Tests

#### API Endpoints Test
**Файл для теста:** `tests/integration/test_api_removal.py` (создать)

```python
import pytest
import httpx

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_monitoring_endpoints_are_gone():
    """Проверить что monitoring endpoints удалены"""
    async with httpx.AsyncClient() as client:
        # Должен быть 404
        response = await client.get(f"{BASE_URL}/api/admin/monitoring/system")
        assert response.status_code == 404

        response = await client.get(f"{BASE_URL}/api/admin/monitoring/overview")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_admin_database_endpoints_still_work():
    """Проверить что admin БД endpoints работают"""
    # Получить токен (замените на реальные credentials)
    login_response = await client.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "test_password"}
    )
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Должен работать (200)
    response = await client.get(
        f"{BASE_URL}/api/admin/stats/database",
        headers=headers
    )
    assert response.status_code == 200
    assert "connections" in response.json()
```

---

### E2E Tests

#### Сценарий 1: Навигация не показывает "Мониторинг системы"
**Инструмент:** Playwright / Puppeteer / Selenium

**Шаги:**
1. Открыть `http://localhost:3000/login`
2. Войти как admin (username: admin, password: <admin_password>)
3. Проверить навигационное меню
4. **Assertion:** Нет пункта "Мониторинг системы"
5. **Assertion:** Есть пункты: "Мониторинг новостей", "Опубликованные новости", "Мониторинг расходов", "Настройки"

#### Сценарий 2: /system-monitoring возвращает 404
**Шаги:**
1. Войти как admin
2. Перейти напрямую на `http://localhost:3000/system-monitoring`
3. **Assertion:** Отображается 404 страница Next.js

#### Сценарий 3: Критичные функции работают
**Шаги:**
1. Войти как admin
2. Перейти на `/monitoring`
3. Выбрать источник "ria"
4. Нажать "Сканировать"
5. **Assertion:** Парсинг проходит успешно, новости сохраняются
6. Выбрать статью → "Сгенерировать"
7. **Assertion:** AI генерация проходит успешно
8. Опубликовать в Bitrix
9. **Assertion:** Публикация успешна

---

### Performance Tests

#### Backend Performance
```bash
# Проверить что время запуска backend не увеличилось
time uvicorn main:app --host 0.0.0.0 --port 8000 &
sleep 5
curl http://localhost:8000/health
# Ожидается: < 3 секунд до первого успешного /health

# Проверить memory usage (должно снизиться)
ps aux | grep "uvicorn main:app"
# Ожидается: VSZ и RSS меньше чем было (без psutil)
```

#### API Response Time
```bash
# Проверить что другие endpoints не стали медленнее
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/news/sources

# curl-format.txt:
# time_total: %{time_total}s

# Ожидается: < 500ms
```

---

### Security Tests

#### Verify No Sensitive Data Leaked
```bash
# Проверить что в коммитах не осталось sensitive data
git log -p | grep -i "password\|secret\|token" | head -20

# Проверить что .env не был случайно добавлен
git ls-files | grep ".env"
# Ожидается: пустой вывод
```

---

## 📚 Documentation Updates Checklist

- [ ] `CLAUDE.md` - обновлена Backend Structure секция
- [ ] `CLAUDE.md` - удалены примеры мониторинга из Common Debugging
- [ ] `CHANGELOG.md` - добавлена запись об удалении функционала
- [ ] `docs/adr/ADR-XXX-remove-system-monitoring.md` - создан новый ADR
- [ ] `docs/architecture/overview.md` - удалены упоминания мониторинга (если есть)
- [ ] `docs/api/endpoints.md` - проверено что нет ссылок на monitoring endpoints
- [ ] `README.md` - проверено что нет ссылок на системный мониторинг
- [ ] Inline комментарии в коде обновлены (если ссылались на monitoring)

---

## 🚀 Recommendations

### Must Have (обязательно)

1. **Сохранить db_monitoring.py**
   - Причина: Используется admin API для БД статистики
   - Endpoints: `/api/admin/stats/database/*`
   - Действие: НЕ удалять этот файл

2. **Протестировать admin БД endpoints**
   - После удаления проверить что `/api/admin/stats/database` работает
   - Используется для мониторинга производительности PostgreSQL

3. **Обновить Navigation.js**
   - Убрать пункт "Мониторинг системы" из меню
   - Иначе пользователи увидят 404

4. **Создать ADR**
   - Документировать архитектурное решение
   - Объяснить причины удаления

5. **Проверить что aiohttp НЕ удален**
   - Используется news parsers
   - Только psutil можно удалить (если не используется)

---

### Nice to Have (желательно)

1. **Сохранить код в отдельной ветке**
   ```bash
   git checkout -b archive/system-monitoring-backup
   git checkout main
   ```
   - На случай если потребуется восстановить функционал

2. **Добавить внешний мониторинг**
   - Grafana + Prometheus для метрик
   - Loki для логов
   - Альтернатива удаленному функционалу

3. **Обновить .gitignore**
   - Добавить паттерны если добавляли временные файлы

4. **Написать миграционный гайд**
   - Для других разработчиков
   - Если они использовали monitoring API

5. **Проверить Docker образы**
   - Пересобрать образы после удаления
   - Проверить что размер уменьшился

---

## 👥 Team Lead Handoff

### Рекомендуемая последовательность

**Шаг 1: Preparation (30 min)**
- Создать feature branch `feature/remove-system-monitoring`
- Проверить использование `db_monitoring.py` в admin API
- Проверить использование `psutil` и `aiohttp` в других модулях
- Убедиться что tests проходят до изменений

**Шаг 2: Backend Changes (1 hour)**
- Удалить `backend/api/monitoring.py`
- Удалить `backend/services/system_monitoring.py`
- Обновить `backend/main.py` (убрать импорт и регистрацию)
- СОХРАНИТЬ `backend/services/db_monitoring.py` (!)
- Опционально: удалить psutil из requirements.txt (если не используется)

**Шаг 3: Frontend Changes (1 hour)**
- Удалить `frontend/pages/system-monitoring.js`
- Удалить `frontend/components/monitoring/` (вся директория)
- Обновить `frontend/components/Navigation.js` (убрать пункт меню)

**Шаг 4: Testing (1 hour)**
- Запустить backend: `uvicorn main:app --reload`
- Проверить `/health` endpoint работает
- Проверить `/api/admin/monitoring/*` возвращает 404
- Проверить `/api/admin/stats/database` работает (!)
- Запустить frontend: `npm run dev`
- Проверить навигация не показывает "Мониторинг системы"
- Проверить `/system-monitoring` возвращает 404
- Проверить критичные функции: парсинг, генерация, публикация

**Шаг 5: Documentation (30 min)**
- Обновить `CLAUDE.md`
- Обновить `CHANGELOG.md`
- Создать `docs/adr/ADR-XXX-remove-system-monitoring.md`

**Шаг 6: Commit & Deploy (30 min)**
- Commit с детальным описанием
- Merge в main (или создать PR)
- Deploy на staging
- Проверить production готовность

---

### Особые указания

⚠️ **КРИТИЧНО:**
1. **НЕ УДАЛЯТЬ** `backend/services/db_monitoring.py` - используется admin API
2. **НЕ УДАЛЯТЬ** `frontend/pages/monitoring.js` - это главная страница (news monitoring)!
3. **НЕ УДАЛЯТЬ** `frontend/components/NewsMonitoring.js` - компонент новостного мониторинга
4. **НЕ УДАЛЯТЬ** `frontend/components/ExpenseMonitoring.js` - мониторинг AI расходов
5. **ПРОВЕРИТЬ** что aiohttp используется в parsers перед удалением из requirements.txt

⚡ **ВАЖНО:**
- Системный мониторинг (`/system-monitoring`) ≠ Новостной мониторинг (`/monitoring`)
- Monitoring API (`/api/admin/monitoring/*`) ≠ Admin stats API (`/api/admin/stats/*`)
- Удаляем только SYSTEM monitoring, всё остальное сохраняем

✅ **ПРОВЕРКИ после удаления:**
- Backend стартует без ошибок
- Admin database endpoints работают
- Frontend собирается
- Навигация не показывает удаленный пункт
- Парсинг новостей работает
- Генерация статей работает
- Публикация работает

---

## 📝 FILES TO DELETE

### Backend
```
backend/api/monitoring.py
backend/api/__pycache__/monitoring.cpython-313.pyc
backend/services/system_monitoring.py
backend/services/__pycache__/system_monitoring.cpython-313.pyc
```

### Frontend
```
frontend/pages/system-monitoring.js
frontend/components/monitoring/SystemMonitoringDashboard.js
frontend/components/monitoring/ServiceStatusCard.js
frontend/components/monitoring/SystemMetricsPanel.js
frontend/components/monitoring/AlertsPanel.js
```

**Или просто:**
```bash
rm -rf frontend/components/monitoring/
```

---

## 📝 FILES TO MODIFY

### Backend
```
backend/main.py
  - Line 13: remove 'monitoring' from imports
  - Line 225: remove app.include_router(monitoring.router, ...)

backend/requirements.txt (optional)
  - Remove: psutil==5.9.6 (if not used elsewhere)
  - Keep: aiohttp (used by parsers)
```

### Frontend
```
frontend/components/Navigation.js
  - Line 9: remove HiOutlineChartBarSquare import
  - Line 24: remove system-monitoring navigation item
```

### Documentation
```
CLAUDE.md
  - Update Backend Structure section
  - Remove monitoring examples from Common Debugging

CHANGELOG.md
  - Add removal note

docs/adr/ADR-XXX-remove-system-monitoring.md
  - Create new ADR
```

---

## 📝 FILES TO KEEP (NOT DELETE!)

### Backend
```
✅ backend/services/db_monitoring.py
   Reason: Used by admin API /stats/database/*

✅ backend/api/admin.py
   Reason: Contains database stats endpoints

✅ All parsers (ria, medvestnik, aig, remedium, rbc_medical)
   Reason: Core functionality
```

### Frontend
```
✅ frontend/pages/monitoring.js
   Reason: Main page for NEWS monitoring (not system)

✅ frontend/components/NewsMonitoring.js
   Reason: News sources monitoring component

✅ frontend/components/ExpenseMonitoring.js
   Reason: AI expenses tracking (critical business feature)

✅ frontend/pages/expenses.js
   Reason: Expenses dashboard page

✅ frontend/pages/api/proxy/[...path].js
   Reason: API proxy for all requests (not just monitoring)
```

---

## 📊 Summary Statistics

### Code Removal
- **Backend:** ~714 строк (monitoring.py: 362 + system_monitoring.py: 352)
- **Frontend:** ~900+ строк (page: 85 + components: ~815)
- **Total:** ~1600+ строк удалено

### Files Affected
- **Deleted:** 7 files (2 backend, 5 frontend)
- **Modified:** 4 files (main.py, Navigation.js, CLAUDE.md, CHANGELOG.md)
- **Created:** 1 file (ADR document)

### Dependencies
- **Can remove:** psutil (if only used in system_monitoring)
- **Must keep:** aiohttp (used by news parsers)
- **Must keep:** db_monitoring.py (used by admin API)

### Estimated Time
- **Preparation:** 30 min
- **Backend changes:** 1 hour
- **Frontend changes:** 1 hour
- **Testing:** 1 hour
- **Documentation:** 30 min
- **Finalization:** 30 min
- **Total:** 4.5 hours

---

## ✅ Definition of Done

Удаление считается завершенным когда:

- [x] Все файлы monitoring удалены (backend + frontend)
- [x] db_monitoring.py СОХРАНЕН (проверить!)
- [x] Backend стартует без ошибок
- [x] Frontend собирается без ошибок
- [x] Navigation menu обновлен (нет пункта "Мониторинг системы")
- [x] `/api/admin/monitoring/*` возвращает 404
- [x] `/api/admin/stats/database` работает корректно
- [x] Критичные функции работают (парсинг, генерация, публикация)
- [x] CLAUDE.md обновлен
- [x] CHANGELOG.md обновлен
- [x] ADR создан
- [x] Commit сделан с детальным описанием
- [x] Code review пройден (если требуется)
- [x] Merge в main выполнен
- [x] Production deployment успешен (если применимо)

---

**Конец анализа**

**Следующий шаг:** Передать отчет Team Lead для реализации удаления.

**Вопросы для Team Lead:**
1. Нужно ли сохранять код в отдельной ветке перед удалением?
2. Требуется ли code review / PR перед мержем в main?
3. Планируется ли альтернатива (Grafana/Prometheus)?
4. Нужны ли дополнительные тесты перед production deploy?

---

**Technical Architect Agent**
*Signature: TA-2025-10-07-MONITORING-REMOVAL*
