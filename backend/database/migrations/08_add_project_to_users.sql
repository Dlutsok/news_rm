-- Добавление поля project к таблице users
-- Это позволит привязывать пользователей к конкретным проектам для автоматического учета расходов

-- Добавляем новое поле project
ALTER TABLE users ADD COLUMN project VARCHAR(50);

-- Создаем индекс для оптимизации запросов по проекту
CREATE INDEX IF NOT EXISTS idx_users_project ON users(project);

-- Добавляем ограничение для валидации проекта
ALTER TABLE users ADD CONSTRAINT chk_users_project_valid 
    CHECK (project IS NULL OR project IN ('gynecology.school', 'therapy.school', 'pediatrics.school', 'rusmedical'));

-- Комментарии к новому полю
COMMENT ON COLUMN users.project IS 'Привязка пользователя к проекту для автоматического учета расходов';

-- Пример обновления существующих пользователей (можно выполнить отдельно)
-- UPDATE users SET project = 'rusmedical' WHERE username = 'admin';
-- UPDATE users SET project = 'gynecology.school' WHERE username LIKE '%gyneco%';
-- UPDATE users SET project = 'pediatrics.school' WHERE username LIKE '%pediatr%';
-- UPDATE users SET project = 'therapy.school' WHERE username LIKE '%therap%';