# Анализ базы данных на сервере 176.124.219.201

## Общая информация

- **Сервер БД**: PostgreSQL 16
- **База данных**: `news_aggregator`
- **Кодировка**: UTF8
- **Локаль**: en_US.UTF-8
- **Общий размер БД**: ~11.3 MB (основные таблицы)

## Структура базы данных

### 1. Основные таблицы и их размеры

| Таблица | Размер | Записей | Назначение |
|---------|---------|---------|------------|
| `articles` | 9.24 MB | 3,280 | Хранение новостных статей |
| `news_generation_drafts` | 984 KB | 152 | Черновики сгенерированных новостей |
| `generation_logs` | 312 KB | 832 | Логи операций генерации контента |
| `expenses` | 216 KB | 275 | Учёт расходов на API |
| `publication_logs` | 208 KB | - | Журнал публикаций в Bitrix |
| `users` | 88 KB | 8 | Пользователи системы |
| `parse_sessions` | 80 KB | - | Сессии парсинга новостей |
| `source_stats` | 72 KB | - | Статистика по источникам |
| `app_settings` | 64 KB | - | Общие настройки приложения |
| `bitrix_project_settings` | 48 KB | - | Настройки проектов Bitrix |

### 2. ENUM типы данных

#### UserRole
```sql
ENUM('ADMIN', 'STAFF', 'ANALYST')
```

#### ProjectType
```sql
ENUM('gynecology.school', 'therapy.school', 'pediatrics.school', 'rusmedical')
```

#### SourceType
```sql
ENUM('RIA', 'MEDVESTNIK', 'AIG', 'REMEDIUM', 'RBC_MEDICAL')
```

## Детальный анализ таблиц

### 1. Таблица `articles` (основная)

**Структура:**
```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    content TEXT,
    source_site sourcetype NOT NULL,
    published_date TIMESTAMP,
    published_time VARCHAR(10),
    views_count INTEGER,
    author VARCHAR(200),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    is_processed BOOLEAN NOT NULL DEFAULT FALSE,
    processing_status VARCHAR(50)
);
```

**Индексы:**
- `PRIMARY KEY (id)`
- `UNIQUE (url)`
- `INDEX (title, created_at, is_processed, published_date, source_site)`

**Статистика по источникам:**
- MEDVESTNIK: 1,258 статей (38.4%)
- RIA: 1,106 статей (33.7%)
- REMEDIUM: 696 статей (21.2%)
- AIG: 127 статей (3.9%)
- RBC_MEDICAL: 93 статьи (2.8%)

**Внешние ключи:**
- Используется в `expenses.related_article_id`
- Используется в `news_generation_drafts.article_id`

### 2. Таблица `users`

**Структура:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role userrole NOT NULL,
    project projecttype,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP
);
```

**Ограничения:**
- Проект может быть NULL или одним из допустимых значений
- CHECK constraint для валидации проекта

**Связи:**
- Связана с `expenses.user_id`
- Связана с `news_generation_drafts.created_by`

### 3. Таблица `news_generation_drafts`

**Структура:**
```sql
CREATE TABLE news_generation_drafts (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id),
    project projecttype NOT NULL,
    summary TEXT NOT NULL,
    facts TEXT NOT NULL,
    generated_news_text TEXT,
    generated_seo_title VARCHAR(200),
    generated_seo_description VARCHAR(500),
    generated_seo_keywords TEXT,
    generated_image_prompt TEXT,
    generated_image_url VARCHAR(1000),
    generated_tg_post TEXT,
    status VARCHAR NOT NULL,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    published_project_code VARCHAR(10),
    published_project_name VARCHAR(100),
    bitrix_id INTEGER,
    published_at TIMESTAMP,
    scheduled_at TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**Ключевые индексы:**
- Множественные индексы по статусу, проекту, дате создания
- Индекс по `bitrix_id` для интеграции с CMS

### 4. Таблица `expenses`

**Структура:**
```sql
CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    project projecttype NOT NULL,
    expense_type VARCHAR(50) NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    description VARCHAR(500),
    related_article_id INTEGER REFERENCES articles(id),
    related_session_id VARCHAR(100),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP
);
```

**Ограничения:**
- CHECK constraint для валидации проекта
- Foreign key constraints для `user_id` и `related_article_id`

### 5. Таблица `generation_logs`

**Структура:**
```sql
CREATE TABLE generation_logs (
    id SERIAL PRIMARY KEY,
    draft_id INTEGER NOT NULL REFERENCES news_generation_drafts(id),
    operation_type VARCHAR(50) NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    tokens_used INTEGER,
    processing_time_seconds DOUBLE PRECISION,
    created_at TIMESTAMP NOT NULL
);
```

**Назначение:** Детальное логирование всех операций с AI для аналитики расходов

## Проблемы и несоответствия с локальными моделями

### 1. Различия в ENUM значениях

**На сервере (БД):**
- SourceType: `'RIA', 'MEDVESTNIK', 'AIG', 'REMEDIUM', 'RBC_MEDICAL'`
- UserRole: `'ADMIN', 'STAFF', 'ANALYST'`
- ProjectType: `'gynecology.school', 'therapy.school', 'pediatrics.school', 'rusmedical'`

**В локальных моделях (models.py):**
```python
class SourceType(str, Enum):
    RIA = "ria"                    # БД: "RIA"
    MEDVESTNIK = "medvestnik"      # БД: "MEDVESTNIK"
    AIG = "aig"                    # БД: "AIG"
    REMEDIUM = "remedium"          # БД: "REMEDIUM"
    RBC_MEDICAL = "rbc_medical"    # БД: "RBC_MEDICAL"

class UserRole(str, Enum):
    ADMIN = "admin"                # БД: "ADMIN"
    STAFF = "staff"                # БД: "STAFF"
    ANALYST = "analyst"            # БД: "ANALYST"

class ProjectType(str, Enum):
    GYNECOLOGY = "gynecology.school"   # БД: "gynecology.school" ✓
    THERAPY = "therapy.school"         # БД: "therapy.school" ✓
    PEDIATRICS = "pediatrics.school"   # БД: "pediatrics.school" ✓
    # Отсутствует "rusmedical" в локальной модели!
```

### 2. Отсутствующие таблицы в локальных моделях

На сервере присутствуют таблицы, которых нет в `models.py`:
- ❌ `telegram_posts` - есть модель, но может отличаться структура
- ❌ `publications` - есть модель, но может отличаться структура

### 3. Различия в структуре полей

**users.project:**
- В БД: `projecttype` (ENUM)
- В модели: `Optional[str]` - неправильный тип!

## Миграции для синхронизации

### Критические миграции для применения:

1. **Исправление ENUM значений** - необходимо привести в соответствие
2. **Добавление недостающих таблиц** (если есть)
3. **Исправление типов полей** (`users.project`)
4. **Добавление `rusmedical` в ProjectType**

### Безопасные миграции:

1. **Добавление новых индексов** (если есть в моделях)
2. **Расширение ограничений** (новые CHECK constraints)
3. **Добавление новых полей** с значениями по умолчанию

## Рекомендации для развертывания

### 1. Стратегия миграций

**Подход "Обратная совместимость":**
```python
# Сначала добавить новые значения ENUM
ALTER TYPE sourcetype ADD VALUE 'ria';
ALTER TYPE sourcetype ADD VALUE 'medvestnik';
# ... и т.д.

# Затем постепенно мигрировать данные
UPDATE articles SET source_site = 'ria' WHERE source_site = 'RIA';

# В конце удалить старые значения
```

### 2. План действий перед развертыванием

1. **Создать полный бэкап БД**
2. **Проанализировать все миграции в `backend/database/migrations/`**
3. **Создать миграцию для синхронизации ENUM типов**
4. **Протестировать миграции на копии БД**
5. **Применить миграции последовательно**

### 3. Критические точки внимания

⚠️ **ВАЖНО:** Изменение ENUM типов в PostgreSQL может заблокировать таблицы!

**Безопасная последовательность:**
1. Добавить новые значения в ENUM
2. Создать миграцию данных
3. Обновить код приложения
4. Удалить старые значения ENUM (опционально)

### 4. Проверочные запросы после миграции

```sql
-- Проверка соответствия ENUM значений
SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'sourcetype');

-- Проверка целостности данных
SELECT source_site, COUNT(*) FROM articles GROUP BY source_site;

-- Проверка внешних ключей
SELECT COUNT(*) FROM news_generation_drafts WHERE article_id NOT IN (SELECT id FROM articles);
```

## Размер и производительность

### Текущие показатели:
- **Общий размер**: ~11.3 MB
- **Самая большая таблица**: `articles` (9.24 MB)
- **Индексация**: Хорошо проиндексированы основные запросы
- **Foreign Keys**: Корректно настроены связи между таблицами

### Рекомендации по производительности:
1. Добавить индексы для частых запросов фильтрации
2. Рассмотреть партиционирование таблицы `articles` по дате
3. Настроить автоочистку старых логов в `generation_logs`

## Заключение

База данных находится в рабочем состоянии с активными данными:
- **3,280 статей** из 5 источников
- **152 черновика** новостей
- **832 лога** операций генерации
- **275 записей** о расходах
- **8 пользователей**

Основная проблема - **несоответствие ENUM значений** между сервером и локальными моделями. Требуется создание миграции для синхронизации перед развертыванием обновленной версии приложения.
