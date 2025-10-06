-- Добавление расширенных системных настроек
-- Добавляет все недостающие системные настройки для полного управления через админ-панель

-- Дополнительные настройки парсинга
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, category, created_at) 
VALUES 
    ('article_content_limit', '6000', 'int', 'Максимальная длина контента статьи в символах', 'system', NOW()),
    ('article_min_paragraph_length', '20', 'int', 'Минимальная длина параграфа для включения в статью', 'system', NOW()),
    ('parsing_max_retries', '3', 'int', 'Максимальное количество попыток парсинга статьи', 'system', NOW())
ON CONFLICT (setting_key) DO NOTHING;

-- Настройки генерации контента
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, category, created_at) 
VALUES 
    ('article_min_length', '2000', 'int', 'Минимальная длина генерируемой статьи в символах', 'system', NOW()),
    ('article_max_length', '4000', 'int', 'Максимальная длина генерируемой статьи в символах', 'system', NOW()),
    ('summary_max_length', '1200', 'int', 'Максимальная длина выжимки статьи в символах', 'system', NOW()),
    ('seo_title_max_length', '60', 'int', 'Максимальная длина SEO заголовка', 'system', NOW()),
    ('seo_description_max_length', '160', 'int', 'Максимальная длина SEO описания', 'system', NOW()),
    ('keywords_count', '7', 'int', 'Количество SEO ключевых слов', 'system', NOW())
ON CONFLICT (setting_key) DO NOTHING;

-- Настройки источников новостей
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, category, created_at) 
VALUES 
    ('medvestnik_enabled', 'true', 'bool', 'Включить парсинг Медвестника', 'system', NOW()),
    ('ria_enabled', 'true', 'bool', 'Включить парсинг РИА Новости', 'system', NOW()),
    ('remedium_enabled', 'true', 'bool', 'Включить парсинг Remedium', 'system', NOW()),
    ('rbc_enabled', 'true', 'bool', 'Включить парсинг РБК', 'system', NOW()),
    ('aig_enabled', 'true', 'bool', 'Включить парсинг AiG', 'system', NOW())
ON CONFLICT (setting_key) DO NOTHING;

-- Настройки фильтрации контента
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, category, created_at) 
VALUES 
    ('content_quality_threshold', '0.7', 'float', 'Порог качества контента (0.0-1.0)', 'system', NOW()),
    ('relevance_threshold', '1', 'int', 'Минимальный балл релевантности для платформы', 'system', NOW()),
    ('duplicate_detection_enabled', 'true', 'bool', 'Включить обнаружение дубликатов', 'system', NOW())
ON CONFLICT (setting_key) DO NOTHING;

-- Настройки мониторинга и метрик
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, category, created_at) 
VALUES 
    ('metrics_enabled', 'true', 'bool', 'Включить сбор метрик', 'system', NOW()),
    ('health_check_interval', '300', 'int', 'Интервал проверки здоровья системы в секундах', 'system', NOW()),
    ('stats_retention_days', '30', 'int', 'Количество дней хранения статистики', 'system', NOW())
ON CONFLICT (setting_key) DO NOTHING;

-- Настройки интеграций
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, category, created_at) 
VALUES 
    ('bitrix_connection_timeout', '30', 'int', 'Таймаут подключения к Bitrix в секундах', 'system', NOW()),
    ('bitrix_retry_attempts', '3', 'int', 'Количество попыток подключения к Bitrix', 'system', NOW())
ON CONFLICT (setting_key) DO NOTHING;

-- Настройки кэширования
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, category, created_at) 
VALUES 
    ('cache_enabled', 'true', 'bool', 'Включить кэширование', 'system', NOW()),
    ('cache_ttl_minutes', '60', 'int', 'Время жизни кэша в минутах', 'system', NOW())
ON CONFLICT (setting_key) DO NOTHING;

-- Настройки безопасности
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, category, created_at) 
VALUES 
    ('rate_limit_requests_per_minute', '100', 'int', 'Лимит запросов в минуту', 'system', NOW()),
    ('api_key_required', 'false', 'bool', 'Требовать API ключ для доступа', 'system', NOW())
ON CONFLICT (setting_key) DO NOTHING;