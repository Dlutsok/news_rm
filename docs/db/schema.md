# Схема базы данных

## Обзор

Система использует SQLite для разработки и PostgreSQL для продакшена. ORM - SQLModel (на основе Pydantic и SQLAlchemy). Все таблицы используют автоинкремент для первичных ключей и включают временные метки.

## Основные таблицы

### articles - Статьи
Хранение новостных статей, собранных из различных источников.

```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    content TEXT,
    source_site VARCHAR(50) NOT NULL,
    published_date DATETIME,
    published_time VARCHAR(10),
    views_count INTEGER,
    author VARCHAR(200),
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc', '+3 hours')),
    updated_at DATETIME,
    is_processed BOOLEAN NOT NULL DEFAULT 0,
    processing_status VARCHAR(50)
);

CREATE INDEX ix_articles_title ON articles (title);
CREATE INDEX ix_articles_url ON articles (url);
CREATE INDEX ix_articles_source_site ON articles (source_site);
CREATE INDEX ix_articles_published_date ON articles (published_date);
CREATE INDEX ix_articles_created_at ON articles (created_at);
CREATE INDEX ix_articles_is_processed ON articles (is_processed);
```

**Поля:**
- `id` - Уникальный идентификатор статьи
- `title` - Заголовок статьи (максимум 500 символов)
- `url` - URL статьи (уникальный, максимум 1000 символов)
- `content` - Полный текст статьи
- `source_site` - Источник статьи (enum: ria, medvestnik, aig, remedium, rbc_medical)
- `published_date` - Дата публикации статьи
- `published_time` - Время публикации в строковом формате
- `views_count` - Количество просмотров статьи
- `author` - Автор статьи
- `created_at` - Время добавления в систему (московское время)
- `updated_at` - Время последнего обновления
- `is_processed` - Флаг обработки статьи
- `processing_status` - Статус обработки

### users - Пользователи
Управление пользователями системы с ролевой моделью.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'staff',
    project VARCHAR(50),
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc', '+3 hours')),
    updated_at DATETIME
);

CREATE INDEX ix_users_username ON users (username);
CREATE INDEX ix_users_role ON users (role);
CREATE INDEX ix_users_project ON users (project);
CREATE INDEX ix_users_created_at ON users (created_at);
```

**Поля:**
- `id` - Уникальный идентификатор пользователя
- `username` - Имя пользователя (уникальное)
- `hashed_password` - Хэшированный пароль (bcrypt)
- `role` - Роль пользователя (admin, staff, analyst)
- `project` - Привязка к проекту
- `created_at` - Время создания аккаунта
- `updated_at` - Время последнего обновления

### news_generation_drafts - Черновики генерации новостей
Хранение промежуточных результатов генерации новостных материалов.

```sql
CREATE TABLE news_generation_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL REFERENCES articles(id),
    project VARCHAR(50) NOT NULL,
    summary TEXT NOT NULL,
    facts TEXT NOT NULL,
    generated_news_text TEXT,
    generated_seo_title VARCHAR(200),
    generated_seo_description VARCHAR(500),
    generated_seo_keywords TEXT,
    generated_image_prompt TEXT,
    generated_image_url VARCHAR(1000),
    generated_tg_post TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'summary_pending',
    is_published BOOLEAN NOT NULL DEFAULT 0,
    published_project_code VARCHAR(10),
    published_project_name VARCHAR(100),
    bitrix_id INTEGER,
    published_at DATETIME,
    scheduled_at DATETIME,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc', '+3 hours')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc', '+3 hours'))
);

CREATE INDEX ix_news_generation_drafts_article_id ON news_generation_drafts (article_id);
CREATE INDEX ix_news_generation_drafts_project ON news_generation_drafts (project);
CREATE INDEX ix_news_generation_drafts_status ON news_generation_drafts (status);
CREATE INDEX ix_news_generation_drafts_is_published ON news_generation_drafts (is_published);
CREATE INDEX ix_news_generation_drafts_bitrix_id ON news_generation_drafts (bitrix_id);
CREATE INDEX ix_news_generation_drafts_published_at ON news_generation_drafts (published_at);
CREATE INDEX ix_news_generation_drafts_scheduled_at ON news_generation_drafts (scheduled_at);
CREATE INDEX ix_news_generation_drafts_created_by ON news_generation_drafts (created_by);
CREATE INDEX ix_news_generation_drafts_created_at ON news_generation_drafts (created_at);
```

**Поля:**
- `id` - Уникальный идентификатор черновика
- `article_id` - Связь с исходной статьей
- `project` - Проект для которого генерируется новость
- `summary` - Краткое изложение статьи
- `facts` - Факты из статьи (JSON строка)
- `generated_news_text` - Сгенерированный текст новости
- `generated_seo_title` - SEO заголовок
- `generated_seo_description` - SEO описание
- `generated_seo_keywords` - SEO ключевые слова (JSON)
- `generated_image_prompt` - Промпт для генерации изображения
- `generated_image_url` - URL сгенерированного изображения
- `generated_tg_post` - Анонс для Telegram
- `status` - Статус обработки (summary_pending, confirmed, generated, scheduled, published)
- `is_published` - Флаг публикации
- `published_project_code` - Код проекта публикации (GS, TS, PS)
- `published_project_name` - Название проекта
- `bitrix_id` - ID в Bitrix CMS
- `published_at` - Время публикации
- `scheduled_at` - Время запланированной публикации (UTC)
- `created_by` - Пользователь создатель
- `created_at` - Время создания
- `updated_at` - Время обновления

### expenses - Расходы
Учет финансовых операций системы.

```sql
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    project VARCHAR(50) NOT NULL,
    expense_type VARCHAR(50) NOT NULL,
    amount FLOAT NOT NULL,
    description VARCHAR(500),
    related_article_id INTEGER REFERENCES articles(id),
    related_session_id VARCHAR(100),
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc', '+3 hours')),
    updated_at DATETIME
);

CREATE INDEX ix_expenses_user_id ON expenses (user_id);
CREATE INDEX ix_expenses_project ON expenses (project);
CREATE INDEX ix_expenses_expense_type ON expenses (expense_type);
CREATE INDEX ix_expenses_amount ON expenses (amount);
CREATE INDEX ix_expenses_created_at ON expenses (created_at);
```

**Поля:**
- `id` - Уникальный идентификатор расхода
- `user_id` - Пользователь инициатор
- `project` - Проект к которому относится расход
- `expense_type` - Тип расхода (news_creation, photo_regeneration, gpt_message)
- `amount` - Сумма в рублях
- `description` - Описание расхода
- `related_article_id` - Связанная статья
- `related_session_id` - ID сессии операции
- `created_at` - Время создания записи
- `updated_at` - Время обновления

## Справочные таблицы

### source_stats - Статистика источников
Аккумулированная статистика по источникам новостей.

```sql
CREATE TABLE source_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_site VARCHAR(50) UNIQUE NOT NULL,
    total_articles INTEGER NOT NULL DEFAULT 0,
    articles_today INTEGER NOT NULL DEFAULT 0,
    articles_this_week INTEGER NOT NULL DEFAULT 0,
    articles_this_month INTEGER NOT NULL DEFAULT 0,
    last_parsed_at DATETIME,
    last_article_date DATETIME,
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc', '+3 hours')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc', '+3 hours'))
);

CREATE INDEX ix_source_stats_source_site ON source_stats (source_site);
```

### parse_sessions - Сессии парсинга
Журнал операций парсинга для мониторинга и отладки.

```sql
CREATE TABLE parse_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_site VARCHAR(50) NOT NULL,
    requested_articles INTEGER NOT NULL DEFAULT 0,
    parsed_articles INTEGER NOT NULL DEFAULT 0,
    saved_articles INTEGER NOT NULL DEFAULT 0,
    duplicate_articles INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'started',
    error_message TEXT,
    started_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc', '+3 hours')),
    completed_at DATETIME,
    duration_seconds INTEGER
);

CREATE INDEX ix_parse_sessions_source_site ON parse_sessions (source_site);
CREATE INDEX ix_parse_sessions_status ON parse_sessions (status);
CREATE INDEX ix_parse_sessions_started_at ON parse_sessions (started_at);
```

### generation_logs - Логи генерации
Детальные логи AI операций для аналитики и отладки.

```sql
CREATE TABLE generation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER NOT NULL REFERENCES news_generation_drafts(id),
    operation_type VARCHAR(50) NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT 1,
    error_message TEXT,
    tokens_used INTEGER,
    processing_time_seconds FLOAT,
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc', '+3 hours'))
);

CREATE INDEX ix_generation_logs_draft_id ON generation_logs (draft_id);
CREATE INDEX ix_generation_logs_operation_type ON generation_logs (operation_type);
CREATE INDEX ix_generation_logs_success ON generation_logs (success);
CREATE INDEX ix_generation_logs_created_at ON generation_logs (created_at);
```

### publication_logs - Журнал публикаций
Журнал успешных публикаций в Bitrix для аналитики.

```sql
CREATE TABLE publication_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER NOT NULL,
    username VARCHAR(100),
    project VARCHAR(200),
    bitrix_id INTEGER,
    url VARCHAR(1000),
    image_url VARCHAR(1000),
    seo_title VARCHAR(300),
    cost_rub INTEGER NOT NULL DEFAULT 0,
    published_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc', '+3 hours'))
);

CREATE INDEX ix_publication_logs_draft_id ON publication_logs (draft_id);
CREATE INDEX ix_publication_logs_username ON publication_logs (username);
CREATE INDEX ix_publication_logs_project ON publication_logs (project);
CREATE INDEX ix_publication_logs_bitrix_id ON publication_logs (bitrix_id);
CREATE INDEX ix_publication_logs_published_at ON publication_logs (published_at);
```

## Конфигурационные таблицы

### bitrix_project_settings - Настройки проектов Bitrix
Конфигурация интеграции с CMS проектами.

```sql
CREATE TABLE bitrix_project_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code VARCHAR(10) UNIQUE NOT NULL,
    project_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    api_url VARCHAR(500),
    api_token VARCHAR(500),
    iblock_id INTEGER DEFAULT 38,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    description VARCHAR(1000),
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc', '+3 hours')),
    updated_at DATETIME
);

CREATE INDEX ix_bitrix_project_settings_project_code ON bitrix_project_settings (project_code);
```

**Стандартные проекты:**
- `GS` - gynecology.school (Гинекология и акушерство)
- `TS` - therapy.school (Терапия)
- `PS` - pediatrics.school (Педиатрия)

### app_settings - Настройки приложения
Общие настройки системы.

```sql
CREATE TABLE app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value VARCHAR(2000),
    setting_type VARCHAR(20) NOT NULL DEFAULT 'string',
    description VARCHAR(500),
    category VARCHAR(50) NOT NULL DEFAULT 'general',
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'utc', '+3 hours')),
    updated_at DATETIME
);

CREATE INDEX ix_app_settings_setting_key ON app_settings (setting_key);
CREATE INDEX ix_app_settings_category ON app_settings (category);
```

**Основные настройки:**
- `openai_model` - Модель OpenAI (gpt-4o, gpt-4o-mini)
- `image_provider` - Провайдер изображений
- `default_max_articles` - Количество статей по умолчанию
- `bitrix_default_iblock_id` - ID инфоблока по умолчанию

## Енумы (Перечисления)

### SourceType
```python
class SourceType(str, Enum):
    RIA = "ria"
    MEDVESTNIK = "medvestnik"
    AIG = "aig"
    REMEDIUM = "remedium"
    RBC_MEDICAL = "rbc_medical"
```

### UserRole
```python
class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"
    ANALYST = "analyst"
```

### ProjectType
```python
class ProjectType(str, Enum):
    GYNECOLOGY = "gynecology.school"
    THERAPY = "therapy.school"
    PEDIATRICS = "pediatrics.school"
    RUSMEDICAL = "rusmedical"
```

### NewsStatus
```python
class NewsStatus(str, Enum):
    SUMMARY_PENDING = "summary_pending"
    CONFIRMED = "confirmed"
    GENERATED = "generated"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
```

### ExpenseType
```python
class ExpenseType(str, Enum):
    NEWS_CREATION = "news_creation"      # 40 рублей
    PHOTO_REGENERATION = "photo_regeneration"  # 10 рублей
    GPT_MESSAGE = "gpt_message"          # 5 рублей
```

## Связи между таблицами

### Основные связи
1. `articles` ← `news_generation_drafts` (один ко многим)
2. `users` ← `news_generation_drafts` (один ко многим)
3. `users` ← `expenses` (один ко многим)
4. `articles` ← `expenses` (один ко многим, опционально)
5. `news_generation_drafts` ← `generation_logs` (один ко многим)

### Диаграмма связей
```
articles
├── news_generation_drafts (article_id)
└── expenses (related_article_id)

users
├── news_generation_drafts (created_by)
└── expenses (user_id)

news_generation_drafts
├── generation_logs (draft_id)
└── publication_logs (draft_id)
```

## Индексы и производительность

### Основные индексы
- Все внешние ключи индексированы
- Временные метки индексированы для сортировки
- Поля поиска (title, url) индексированы
- Статусные поля индексированы для фильтрации

### Составные индексы (рекомендуемые для продакшена)
```sql
-- Для поиска статей по источнику и дате
CREATE INDEX ix_articles_source_date ON articles (source_site, created_at);

-- Для аналитики расходов
CREATE INDEX ix_expenses_project_type_date ON expenses (project, expense_type, created_at);

-- Для мониторинга генерации
CREATE INDEX ix_generation_logs_operation_success ON generation_logs (operation_type, success, created_at);
```

## Ограничения и правила

### Ограничения целостности
- URL статей должны быть уникальными
- Имена пользователей должны быть уникальными
- Коды проектов Bitrix должны быть уникальными
- Ключи настроек должны быть уникальными

### Правила валидации
- Заголовки статей не должны превышать 500 символов
- URL не должны превышать 1000 символов
- Роли пользователей ограничены enum значениями
- Типы расходов ограничены enum значениями

### Каскадные операции
- При удалении пользователя, его расходы сохраняются (soft delete)
- При удалении статьи, связанные черновики требуют ручной обработки
- Логи операций никогда не удаляются автоматически

## Миграции

### Управление миграциями
Система использует Alembic для управления миграциями базы данных:

```bash
# Создание новой миграции
alembic revision --autogenerate -m "Описание изменения"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

### История версий
- v1.0 - Базовая схема с таблицами articles, users
- v1.1 - Добавление news_generation_drafts, expenses
- v1.2 - Добавление логирования и аналитики
- v1.3 - Конфигурационные таблицы и настройки

## Резервное копирование

### Стратегия бэкапов
- Ежедневные полные бэкапы в 03:00 MSK
- Инкрементальные бэкапы каждые 6 часов
- Хранение бэкапов в течение 30 дней
- Тестирование восстановления еженедельно

### Команды бэкапа (SQLite)
```bash
# Создание бэкапа
sqlite3 database.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"

# Восстановление
sqlite3 new_database.db ".restore backup_file.db"
```

### Команды бэкапа (PostgreSQL)
```bash
# Создание бэкапа
pg_dump -h localhost -U user -d database_name > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление
psql -h localhost -U user -d database_name < backup_file.sql
```

## Мониторинг базы данных

### Ключевые метрики
- Размер базы данных
- Количество записей в основных таблицах
- Время выполнения запросов
- Количество подключений
- Использование индексов

### Запросы для мониторинга
```sql
-- Размер таблиц (SQLite)
SELECT name, COUNT(*) as row_count
FROM sqlite_master m
JOIN sqlite_stat1 s ON m.name = s.tbl
WHERE m.type = 'table';

-- Статистика по источникам
SELECT source_site, COUNT(*) as count, MAX(created_at) as last_update
FROM articles
GROUP BY source_site;

-- Активность пользователей
SELECT u.username, COUNT(e.id) as operations_count, SUM(e.amount) as total_cost
FROM users u
LEFT JOIN expenses e ON u.id = e.user_id
WHERE e.created_at >= date('now', '-7 days')
GROUP BY u.id, u.username;
```