-- Инициализация системных настроек
-- Создание базовых системных настроек для управления через админ-панель

-- Системные настройки
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, category, created_at) 
VALUES 
    ('log_level', 'INFO', 'string', 'Уровень логирования (DEBUG, INFO, WARNING, ERROR)', 'system', NOW()),
    ('debug_mode', 'false', 'bool', 'Режим отладки', 'system', NOW()),
    ('request_timeout', '30', 'int', 'Таймаут HTTP запросов в секундах', 'system', NOW()),
    ('max_concurrent_requests', '10', 'int', 'Максимальное количество одновременных запросов', 'system', NOW())
ON CONFLICT (setting_key) DO NOTHING;

-- Настройки парсинга
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, category, created_at) 
VALUES 
    ('news_parsing_limit', '100', 'int', 'Лимит новостей для парсинга за раз', 'system', NOW()),
    ('parsing_days_back', '7', 'int', 'Количество дней назад для парсинга новостей', 'system', NOW()),
    ('parsing_timeout_seconds', '30', 'int', 'Таймаут для парсинга одной статьи в секундах', 'system', NOW())
ON CONFLICT (setting_key) DO NOTHING;

-- Настройки публикации
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, category, created_at) 
VALUES 
    ('auto_publish_enabled', 'false', 'bool', 'Автоматическая публикация статей', 'system', NOW()),
    ('max_daily_publications', '10', 'int', 'Максимальное количество публикаций в день', 'system', NOW()),
    ('publish_delay_minutes', '30', 'int', 'Задержка между публикациями в минутах', 'system', NOW())
ON CONFLICT (setting_key) DO NOTHING;