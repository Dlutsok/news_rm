-- Создание таблицы пользователей (users)
-- Используется для ручного создания таблицы в случае проблем с автоматической инициализацией

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'staff',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Создание индексов
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Вставка администратора по умолчанию (пароль: admin123)
INSERT INTO users (username, hashed_password, role) 
VALUES ('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Комментарии к таблице
COMMENT ON TABLE users IS 'Таблица пользователей системы';
COMMENT ON COLUMN users.id IS 'Уникальный идентификатор пользователя';
COMMENT ON COLUMN users.username IS 'Имя пользователя (логин)';
COMMENT ON COLUMN users.hashed_password IS 'Хэш пароля (bcrypt)';
COMMENT ON COLUMN users.role IS 'Роль пользователя: admin или staff';
COMMENT ON COLUMN users.created_at IS 'Дата создания записи';
COMMENT ON COLUMN users.updated_at IS 'Дата последнего обновления';