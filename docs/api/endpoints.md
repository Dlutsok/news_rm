# API Endpoints - Документация

## Обзор API

Система предоставляет REST API для управления новостями, пользователями, настройками и мониторингом. Все API используют JSON формат данных и требуют аутентификации через JWT токены (кроме публичных эндпоинтов).

**Base URL:** `http://localhost:8000` (development) / `https://yourdomain.com` (production)

## Аутентификация

### POST /api/auth/login
Вход в систему

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### GET /api/auth/me
Получение информации о текущем пользователе

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "role": "admin",
  "project": "gynecology.school",
  "created_at": "2024-01-01T00:00:00"
}
```

## Новости и парсинг

### GET /api/news/sources
Получить список доступных источников новостей

**Response:**
```json
["ria", "medvestnik", "aig", "remedium", "rbc_medical"]
```

### GET /api/news/sources/info
Получение информации о всех парсерах

**Response:**
```json
{
  "ria": {
    "name": "РИА Новости",
    "description": "Российское информационное агентство",
    "status": "active",
    "last_update": "2024-01-01T12:00:00"
  },
  "medvestnik": {
    "name": "Медвестник",
    "description": "Медицинский портал",
    "status": "active",
    "last_update": "2024-01-01T11:30:00"
  }
}
```

### GET /api/news/sources/test
Тестирование парсера новостей

**Response:**
```json
{
  "status": "success",
  "message": "Парсер работает! Найдено 3 новостей из ria",
  "sample_titles": [
    "Новость 1",
    "Новость 2",
    "Новость 3"
  ],
  "total_found": 3,
  "tested_source": "ria"
}
```

### POST /api/news/parse
Парсинг новостей из выбранных источников

**Request Body:**
```json
{
  "sources": ["ria", "medvestnik"],
  "max_articles": 10,
  "date_filter": "today",
  "fetch_full_content": true,
  "combine_results": false
}
```

**Response:**
```json
{
  "status": "success",
  "total_articles": 15,
  "results": {
    "ria": {
      "articles": [...],
      "count": 8
    },
    "medvestnik": {
      "articles": [...],
      "count": 7
    }
  }
}
```

### POST /api/news/parse-to-db
Парсинг и сохранение новостей в базу данных

**Request Body:**
```json
{
  "sources": ["ria"],
  "max_articles": 20
}
```

**Response:**
```json
{
  "status": "success",
  "results": {
    "ria": {
      "parsed": 20,
      "saved": 18,
      "duplicates": 2,
      "session_id": 123
    }
  }
}
```

### GET /api/news/articles
Получение списка статей из базы данных

**Query Parameters:**
- `source` (optional): фильтр по источнику
- `limit` (optional, default=50): количество статей
- `offset` (optional, default=0): смещение
- `search` (optional): поиск по заголовку

**Response:**
```json
{
  "articles": [
    {
      "id": 1,
      "title": "Заголовок статьи",
      "url": "https://...",
      "source_site": "ria",
      "published_date": "2024-01-01T12:00:00",
      "created_at": "2024-01-01T12:05:00",
      "is_processed": false
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### GET /api/news/articles/{article_id}
Получение детальной информации о статье

**Response:**
```json
{
  "id": 1,
  "title": "Заголовок статьи",
  "url": "https://...",
  "content": "Полный текст статьи...",
  "source_site": "ria",
  "published_date": "2024-01-01T12:00:00",
  "author": "Автор",
  "views_count": 1500,
  "created_at": "2024-01-01T12:05:00",
  "is_processed": true
}
```

### GET /api/news/stats
Статистика по источникам

**Response:**
```json
{
  "sources": [
    {
      "source_site": "ria",
      "total_articles": 1250,
      "articles_today": 15,
      "articles_this_week": 85,
      "articles_this_month": 320,
      "last_parsed_at": "2024-01-01T12:00:00"
    }
  ],
  "totals": {
    "total_articles": 5000,
    "articles_today": 45,
    "articles_this_week": 280
  }
}
```

### GET /api/news/parse-sessions
История сессий парсинга

**Query Parameters:**
- `limit` (optional, default=20)
- `source` (optional): фильтр по источнику

**Response:**
```json
{
  "sessions": [
    {
      "id": 123,
      "source_site": "ria",
      "requested_articles": 20,
      "parsed_articles": 20,
      "saved_articles": 18,
      "duplicate_articles": 2,
      "status": "completed",
      "started_at": "2024-01-01T12:00:00",
      "completed_at": "2024-01-01T12:02:30",
      "duration_seconds": 150
    }
  ]
}
```

## Генерация новостей

### POST /api/news-generation/generate-summary
Создание выжимки из статьи

**Request Body:**
```json
{
  "article_id": 123,
  "project": "gynecology.school"
}
```

**Response:**
```json
{
  "status": "success",
  "draft_id": 456,
  "summary": "Краткое изложение статьи...",
  "facts": ["Факт 1", "Факт 2", "Факт 3"]
}
```

### POST /api/news-generation/confirm-summary
Подтверждение выжимки и запуск генерации

**Request Body:**
```json
{
  "draft_id": 456,
  "confirmed_summary": "Отредактированная выжимка...",
  "confirmed_facts": ["Факт 1", "Факт 2"]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Генерация запущена",
  "draft_id": 456
}
```

### GET /api/news-generation/drafts
Список черновиков новостей

**Query Parameters:**
- `status` (optional): фильтр по статусу
- `project` (optional): фильтр по проекту
- `limit` (optional, default=20)

**Response:**
```json
{
  "drafts": [
    {
      "id": 456,
      "article_id": 123,
      "project": "gynecology.school",
      "summary": "Выжимка...",
      "status": "generated",
      "created_at": "2024-01-01T12:00:00",
      "generated_news_text": "Сгенерированная новость...",
      "generated_seo_title": "SEO заголовок",
      "generated_image_url": "https://..."
    }
  ]
}
```

### GET /api/news-generation/drafts/{draft_id}
Получение детальной информации о черновике

**Response:**
```json
{
  "id": 456,
  "article_id": 123,
  "project": "gynecology.school",
  "summary": "Выжимка...",
  "facts": ["Факт 1", "Факт 2"],
  "generated_news_text": "Полный текст новости...",
  "generated_seo_title": "SEO заголовок",
  "generated_seo_description": "SEO описание",
  "generated_seo_keywords": ["ключевое слово 1", "ключевое слово 2"],
  "generated_image_prompt": "Промпт для изображения",
  "generated_image_url": "https://...",
  "generated_tg_post": "Анонс для Telegram",
  "status": "generated",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:05:00"
}
```

### POST /api/news-generation/regenerate-image
Перегенерация изображения для новости

**Request Body:**
```json
{
  "draft_id": 456,
  "new_prompt": "Новый промпт для изображения"
}
```

**Response:**
```json
{
  "status": "success",
  "new_image_url": "https://...",
  "cost": 10
}
```

### POST /api/news-generation/publish
Публикация новости в Bitrix

**Request Body:**
```json
{
  "draft_id": 456,
  "bitrix_project_code": "GS",
  "schedule_at": null
}
```

**Response:**
```json
{
  "status": "success",
  "bitrix_id": 789,
  "url": "https://gynecology.school/news/789",
  "cost": 30
}
```

### POST /api/news-generation/schedule
Планирование отложенной публикации

**Request Body:**
```json
{
  "draft_id": 456,
  "scheduled_at": "2024-01-02T10:00:00",
  "bitrix_project_code": "GS"
}
```

## Пользователи

### GET /api/users
Список пользователей (только для админов)

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "role": "admin",
      "project": null,
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

### POST /api/users
Создание нового пользователя

**Request Body:**
```json
{
  "username": "newuser",
  "password": "securepassword",
  "role": "staff",
  "project": "therapy.school"
}
```

### PUT /api/users/{user_id}
Обновление пользователя

**Request Body:**
```json
{
  "role": "analyst",
  "project": "pediatrics.school"
}
```

### DELETE /api/users/{user_id}
Удаление пользователя

## Расходы

### GET /api/expenses
Список расходов

**Query Parameters:**
- `user_id` (optional): фильтр по пользователю
- `project` (optional): фильтр по проекту
- `expense_type` (optional): фильтр по типу расхода
- `date_from` (optional): дата начала
- `date_to` (optional): дата окончания
- `limit` (optional, default=50)

**Response:**
```json
{
  "expenses": [
    {
      "id": 1,
      "user_id": 1,
      "user_name": "admin",
      "project": "gynecology.school",
      "expense_type": "news_creation",
      "amount": 30.0,
      "description": "Создание новости #456",
      "created_at": "2024-01-01T12:00:00"
    }
  ],
  "total_amount": 150.0,
  "expenses_count": 5
}
```

### GET /api/expenses/summary
Сводка расходов

**Query Parameters:**
- `period` (optional): day, week, month, year
- `user_id` (optional)
- `project` (optional)

**Response:**
```json
{
  "total_amount": 1500.0,
  "expenses_count": 50,
  "by_project": {
    "gynecology.school": 800.0,
    "therapy.school": 500.0,
    "pediatrics.school": 200.0
  },
  "by_user": {
    "admin": 900.0,
    "editor1": 600.0
  },
  "by_type": {
    "news_creation": 1200.0,
    "photo_regeneration": 200.0,
    "gpt_message": 100.0
  }
}
```

### POST /api/expenses
Создание записи о расходах

**Request Body:**
```json
{
  "user_id": 1,
  "project": "gynecology.school",
  "expense_type": "news_creation",
  "amount": 30.0,
  "description": "Описание расхода",
  "related_article_id": 123
}
```

## Настройки

### GET /api/settings
Получение всех настроек

**Response:**
```json
{
  "bitrix_projects": [
    {
      "project_code": "GS",
      "project_name": "gynecology.school",
      "display_name": "Гинекология и акушерство",
      "api_url": "https://...",
      "is_active": true
    }
  ],
  "app_settings": {
    "openai_model": "gpt-4o",
    "image_provider": "openai_dall_e",
    "default_max_articles": 20
  }
}
```

### PUT /api/settings/bitrix-projects/{project_code}
Обновление настроек Bitrix проекта

**Request Body:**
```json
{
  "api_url": "https://new-api-url.com",
  "api_token": "new-token",
  "is_active": true
}
```

### PUT /api/settings/app/{setting_key}
Обновление настройки приложения

**Request Body:**
```json
{
  "setting_value": "gpt-4o-mini",
  "setting_type": "string"
}
```

## Мониторинг

### GET /api/admin/monitoring/system-info
Информация о системе

**Response:**
```json
{
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 67.8,
    "disk_percent": 23.4,
    "uptime": "2 days, 5:30:00"
  },
  "database": {
    "total_articles": 5000,
    "total_users": 10,
    "total_drafts": 250,
    "database_size": "125.6 MB"
  },
  "ai_usage": {
    "total_requests_today": 45,
    "total_tokens_today": 125000,
    "total_cost_today": 150.0
  }
}
```

### GET /api/admin/monitoring/parse-sessions
Мониторинг сессий парсинга

**Response:**
```json
{
  "recent_sessions": [...],
  "success_rate": 95.5,
  "avg_duration": 120,
  "total_sessions_today": 10
}
```

### GET /api/admin/monitoring/health
Проверка здоровья системы

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "ai_service": "ok",
    "parsers": "ok",
    "disk_space": "warning"
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

### GET /api/admin/users/activity
Активность пользователей

**Response:**
```json
{
  "active_users_today": 5,
  "total_operations_today": 120,
  "by_user": [
    {
      "username": "admin",
      "operations_today": 50,
      "last_activity": "2024-01-01T12:00:00"
    }
  ]
}
```

## Изображения

### POST /api/images/generate
Генерация изображения

**Request Body:**
```json
{
  "prompt": "Медицинская тематика, современная клиника",
  "provider": "openai_dall_e",
  "size": "1024x1024"
}
```

**Response:**
```json
{
  "status": "success",
  "image_url": "http://localhost:8000/api/images/storage/images/generated_123.png",
  "cost": 10,
  "provider": "openai_dall_e"
}
```

### GET /api/images/storage/images/{filename}
Получение сгенерированного изображения

**Response:** Файл изображения

## Telegram посты

### POST /api/telegram-posts/generate
Генерация Telegram поста для новости

**Request Body:**
```json
{
  "news_draft_id": 456,
  "hook_type": "question",
  "disclosure_level": "hint",
  "call_to_action": "curiosity",
  "include_image": true
}
```

**Response:**
```json
{
  "status": "success",
  "post_id": 789,
  "post_text": "Текст поста для Telegram...",
  "character_count": 850
}
```

### GET /api/telegram-posts/{post_id}
Получение Telegram поста по ID

**Response:**
```json
{
  "id": 789,
  "news_draft_id": 456,
  "hook_type": "question",
  "disclosure_level": "hint",
  "call_to_action": "curiosity",
  "include_image": true,
  "post_text": "Текст поста...",
  "character_count": 850,
  "is_published": false,
  "published_at": null,
  "telegram_message_id": null,
  "created_at": "2024-01-01T12:00:00"
}
```

## URL Articles (Генерация из внешних URL)

### POST /api/url-articles/parse
Парсинг статьи из внешнего URL

**Request Body:**
```json
{
  "url": "https://example.com/article"
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com/article",
  "content": "Markdown контент статьи...",
  "domain": "example.com",
  "article_id": 123,
  "title": "Заголовок статьи",
  "error": null
}
```

### POST /api/url-articles/generate-from-url
Полный цикл генерации статьи из URL

**Request Body:**
```json
{
  "url": "https://example.com/article",
  "project": "gynecology.school",
  "generate_image": true,
  "formatting_options": {
    "include_sources": true,
    "add_expert_opinion": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "draft_id": 456,
  "source_url": "https://example.com/article",
  "source_domain": "example.com",
  "news_text": "Сгенерированная статья...",
  "seo_title": "SEO заголовок",
  "seo_description": "SEO описание",
  "seo_keywords": ["keyword1", "keyword2"],
  "image_url": "https://...",
  "error": null
}
```

## Дополнительные эндпоинты

### POST /api/auth/verify-token
Проверка валидности JWT токена

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "valid": true,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "project": "gynecology.school"
  }
}
```

### POST /api/news/parse-with-batch-save
Парсинг с промежуточным сохранением пакетами

**Request Body:**
```json
{
  "sources": ["ria"],
  "max_articles": 100,
  "fetch_full_content": true
}
```

**Response:**
```json
{
  "status": "success",
  "sources": {
    "ria": {
      "status": "success",
      "parsed": 100,
      "saved": 95,
      "duplicates": 5,
      "errors": 0
    }
  },
  "total_parsed": 100,
  "total_saved": 95,
  "total_duplicates": 5,
  "total_errors": 0
}
```

### GET /api/news/articles-with-publication-status
Получение статей с информацией о публикациях

**Query Parameters:**
- `source` (optional): фильтр по источнику
- `limit` (optional, default=1000): количество статей
- `offset` (optional, default=0): смещение

**Response:**
```json
{
  "articles": [
    {
      "id": 123,
      "title": "Заголовок",
      "url": "https://...",
      "source": "ria",
      "published_date": "2024-01-01T12:00:00",
      "is_published": true,
      "is_scheduled": false,
      "has_draft": true,
      "draft_id": 456,
      "published_projects": [
        {
          "project_code": "GS",
          "project_name": "Gynecology School",
          "bitrix_id": 789,
          "published_at": "2024-01-02T10:00:00"
        }
      ]
    }
  ]
}
```

### GET /api/news/draft/{draft_id}
Получение черновика для редактирования

**Response:**
```json
{
  "id": 456,
  "article_id": 123,
  "project": "gynecology.school",
  "summary": "Выжимка...",
  "facts": "[]",
  "generated_news_text": "Текст новости...",
  "generated_seo_title": "SEO заголовок",
  "generated_seo_description": "SEO описание",
  "generated_seo_keywords": "[]",
  "generated_image_prompt": "Промпт...",
  "generated_image_url": "https://...",
  "status": "generated",
  "scheduled_at": null,
  "is_published": false,
  "created_at": "2024-01-01T12:00:00"
}
```

### DELETE /api/news/article/{article_id}
Удаление статьи по ID

**Response:**
```json
{
  "message": "Article 123 deleted successfully"
}
```

### DELETE /api/news/articles/source/{source}
Удаление всех статей из источника

**Response:**
```json
{
  "message": "Successfully deleted articles from ria",
  "deleted_count": 150
}
```

## Коды ошибок

### Стандартные HTTP коды
- `200 OK` - Успешный запрос
- `201 Created` - Ресурс создан
- `400 Bad Request` - Неверный запрос
- `401 Unauthorized` - Требуется аутентификация
- `403 Forbidden` - Недостаточно прав
- `404 Not Found` - Ресурс не найден
- `408 Request Timeout` - Таймаут запроса
- `422 Unprocessable Entity` - Ошибка валидации
- `500 Internal Server Error` - Внутренняя ошибка сервера

### Пользовательские ошибки
```json
{
  "detail": "Описание ошибки",
  "error_code": "CUSTOM_ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00"
}
```

## Rate Limiting

API использует ограничения частоты запросов:
- **Общие запросы:** 100 запросов в минуту
- **AI операции:** 10 запросов в минуту
- **Парсинг:** 5 запросов в минуту

При превышении лимита возвращается код `429 Too Many Requests`.

## Аутентификация и авторизация

### Роли пользователей
- **admin** - полный доступ ко всем функциям
- **staff** - доступ к созданию и управлению новостями
- **analyst** - доступ только к просмотру и аналитике

### Защищенные эндпоинты
Большинство эндпоинтов требуют JWT токен в заголовке:
```
Authorization: Bearer <jwt_token>
```

### Публичные эндпоинты
- `GET /health`
- `GET /api/health`
- `POST /api/auth/login`