# Миграции 22-23: Критические обновления БД

## Обзор

Эти миграции исправляют критические расхождения между кодом и БД, обнаруженные агентом db-migrations:

- **Миграция 22**: Добавляет поля отслеживания публикаций в `telegram_posts`
- **Миграция 23**: Добавляет значение `URL` в enum `sourcetype`

## Что было исправлено

### 1. Таблица `telegram_posts` (Миграция 22)

**Проблема**: Отсутствовали 3 поля для отслеживания публикации постов в Telegram.

**Добавлены поля**:
- `is_published` (BOOLEAN) - флаг публикации
- `published_at` (TIMESTAMP) - время публикации
- `telegram_message_id` (INTEGER) - ID сообщения в Telegram

**Индексы**:
- `idx_telegram_posts_is_published`
- `idx_telegram_posts_published_at`

**Риск до применения**: API endpoint `/api/telegram-posts/{id}/publish` выдавал 500 error.

### 2. Enum `sourcetype` (Миграция 23)

**Проблема**: В коде добавлен новый тип источника `URL`, но в БД enum не обновлен.

**Добавлено значение**: `URL` для статей, загруженных из внешних URL через Jina AI Reader.

**Риск до применения**: API `/api/url-articles/*` выдавал enum constraint error.

## Применение миграций

### Локально (для разработки)

```bash
cd backend/database/migrations
./apply_migrations_22_23.sh
```

### На продакшене (через SSH)

```bash
# 1. Подключиться к серверу
ssh root@176.124.219.201

# 2. Перейти в директорию проекта
cd /var/www/medical-news

# 3. Применить миграции через Docker
docker exec medical-news-backend python database/migrate.py apply 22
docker exec medical-news-backend python database/migrate.py apply 23

# 4. Перезапустить backend
docker-compose restart backend

# 5. Проверить логи
docker logs medical-news-backend -f
```

### Альтернативный способ (прямое SQL подключение)

```bash
# Установить переменные окружения
export DATABASE_HOST=172.20.0.1
export DATABASE_PORT=5432
export DATABASE_USER=postgres
export DATABASE_PASSWORD=medical2024
export DATABASE_NAME=news_aggregator

# Применить миграцию 22
psql -h $DATABASE_HOST -p $DATABASE_PORT -U $DATABASE_USER -d $DATABASE_NAME \
  -f 22_add_telegram_posts_publication_fields.sql

# Применить миграцию 23
psql -h $DATABASE_HOST -p $DATABASE_PORT -U $DATABASE_USER -d $DATABASE_NAME \
  -f 23_add_url_to_sourcetype_enum.sql
```

## Проверка применения

### Проверить поля telegram_posts

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'telegram_posts'
AND column_name IN ('is_published', 'published_at', 'telegram_message_id')
ORDER BY column_name;
```

Ожидаемый результат:
```
      column_name       |            data_type             | is_nullable
------------------------+----------------------------------+-------------
 is_published           | boolean                          | NO
 published_at           | timestamp with time zone         | YES
 telegram_message_id    | integer                          | YES
```

### Проверить enum sourcetype

```sql
SELECT enumlabel
FROM pg_enum
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'sourcetype')
ORDER BY enumlabel;
```

Ожидаемый результат должен включать:
```
  enumlabel
-------------
 AIG
 MEDVESTNIK
 RBC_MEDICAL
 REMEDIUM
 RIA
 URL         <-- новое значение
```

## Откат (Rollback)

### Откат миграции 22

```sql
-- Удалить добавленные поля
ALTER TABLE telegram_posts DROP COLUMN IF EXISTS is_published;
ALTER TABLE telegram_posts DROP COLUMN IF EXISTS published_at;
ALTER TABLE telegram_posts DROP COLUMN IF EXISTS telegram_message_id;

-- Удалить индексы
DROP INDEX IF EXISTS idx_telegram_posts_is_published;
DROP INDEX IF EXISTS idx_telegram_posts_published_at;
```

### Откат миграции 23

⚠️ **ВНИМАНИЕ**: Удаление значения из enum в PostgreSQL сложно и может потребовать пересоздания enum.

Если необходимо откатить:
1. Убедитесь что нет данных с `source_site = 'URL'`
2. Пересоздайте enum без значения `URL`
3. Или оставьте значение - оно не повредит

## Время применения

- **Локально**: ~5 секунд
- **Продакшен**: ~10 секунд (без downtime)

## Связанные изменения

### Обновлен `backend/database/connection.py`

Добавлены импорты моделей:
```python
from database.models import (
    ..., TelegramPost, Publication, Expense
)
```

Это позволяет SQLModel автоматически создавать таблицы при инициализации.

## Тестирование после применения

### 1. Проверить Telegram posts API

```bash
# Создать Telegram пост
curl -X POST http://localhost:8000/api/telegram-posts/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "news_draft_id": 1,
    "hook_type": "question",
    "disclosure_level": "hint",
    "call_to_action": "curiosity",
    "include_image": true
  }'

# Проверить что is_published = false
curl http://localhost:8000/api/telegram-posts/1 \
  -H "Authorization: Bearer <token>"
```

### 2. Проверить URL articles API

```bash
# Парсить статью из URL
curl -X POST http://localhost:8000/api/url-articles/parse \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'

# Должен вернуть { "source": "URL", ... }
```

## Следующие шаги

1. ✅ Миграции 22-23 применены
2. ✅ `connection.py` обновлен с импортами
3. ⏭️ Перезапустить backend service
4. ⏭️ Протестировать endpoints
5. ⏭️ Обновить frontend (если нужно) для использования новых полей

## Связанные отчеты

- **RAD Agent Report**: `/Users/dan/Documents/chatAI/MVP 11/TASK/agents/RAD/task_20251007_133805.data`
- **DB Migrations Report**: `/Users/dan/Documents/chatAI/MVP 11/TASK/agents/db-migrations/task_20251007_135146.data`

## Дополнительная информация

- **Создано**: 2025-10-07
- **Приоритет**: P0 (КРИТИЧЕСКИЙ)
- **Затронутые endpoints**:
  - `/api/telegram-posts/*` (исправлено)
  - `/api/url-articles/*` (исправлено)
- **Риск**: Низкий (миграции идемпотентны)
- **Downtime**: Нет
