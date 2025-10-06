-- Пересоздание enum для исправления кэша SQLAlchemy
-- Удаляем ограничения, изменяем типы, пересоздаем enum

-- Удаляем ограничения
ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_users_project_valid;
ALTER TABLE expenses DROP CONSTRAINT IF EXISTS chk_expenses_project_valid;

-- Изменяем типы колонок на VARCHAR
ALTER TABLE users ALTER COLUMN project TYPE VARCHAR(50);
ALTER TABLE expenses ALTER COLUMN project TYPE VARCHAR(50);
ALTER TABLE news_generation_drafts ALTER COLUMN project TYPE VARCHAR(50);

-- Дропаем старый enum
DROP TYPE IF EXISTS projecttype CASCADE;

-- Создаем новый enum с теми же значениями
CREATE TYPE projecttype AS ENUM (
    'gynecology.school',
    'therapy.school',
    'pediatrics.school',
    'rusmedical'
);

-- Возвращаем типы колонок к enum
ALTER TABLE users ALTER COLUMN project TYPE projecttype USING project::projecttype;
ALTER TABLE expenses ALTER COLUMN project TYPE projecttype USING project::projecttype;
ALTER TABLE news_generation_drafts ALTER COLUMN project TYPE projecttype USING project::projecttype;

-- Добавляем ограничения обратно
ALTER TABLE users ADD CONSTRAINT chk_users_project_valid 
    CHECK (project IS NULL OR project IN ('gynecology.school', 'therapy.school', 'pediatrics.school', 'rusmedical'));

ALTER TABLE expenses ADD CONSTRAINT chk_expenses_project_valid 
    CHECK (project IN ('gynecology.school', 'therapy.school', 'pediatrics.school', 'rusmedical'));