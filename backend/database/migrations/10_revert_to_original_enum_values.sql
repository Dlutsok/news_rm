-- Возврат к оригинальным значениям enum для совместимости
-- Изменяем типы колонок на VARCHAR, обновляем значения, потом возвращаем обратно

-- Шаг 1: Изменяем типы колонок на VARCHAR
ALTER TABLE users ALTER COLUMN project TYPE VARCHAR(50);
ALTER TABLE news_generation_drafts ALTER COLUMN project TYPE VARCHAR(50);

-- Шаг 2: Обновляем значения в users
UPDATE users SET project = 'gynecology.school' WHERE project = 'GYNECOLOGY';
UPDATE users SET project = 'therapy.school' WHERE project = 'THERAPY';
UPDATE users SET project = 'pediatrics.school' WHERE project = 'PEDIATRICS';  
UPDATE users SET project = 'rusmedical' WHERE project = 'RUSMEDICAL';

-- Шаг 3: Обновляем значения в expenses (уже VARCHAR)
UPDATE expenses SET project = 'gynecology.school' WHERE project = 'GYNECOLOGY';
UPDATE expenses SET project = 'therapy.school' WHERE project = 'THERAPY';
UPDATE expenses SET project = 'pediatrics.school' WHERE project = 'PEDIATRICS';
UPDATE expenses SET project = 'rusmedical' WHERE project = 'RUSMEDICAL';

-- Шаг 4: Обновляем значения в news_generation_drafts
UPDATE news_generation_drafts SET project = 'gynecology.school' WHERE project = 'GYNECOLOGY';
UPDATE news_generation_drafts SET project = 'therapy.school' WHERE project = 'THERAPY';
UPDATE news_generation_drafts SET project = 'pediatrics.school' WHERE project = 'PEDIATRICS';
UPDATE news_generation_drafts SET project = 'rusmedical' WHERE project = 'RUSMEDICAL';

-- Шаг 5: Удаляем старый enum
DROP TYPE IF EXISTS projecttype CASCADE;

-- Шаг 6: Создаем новый enum с правильными значениями
CREATE TYPE projecttype AS ENUM (
    'gynecology.school',
    'therapy.school', 
    'pediatrics.school',
    'rusmedical'
);

-- Шаг 7: Возвращаем типы колонок обратно к enum
ALTER TABLE users ALTER COLUMN project TYPE projecttype USING project::projecttype;
ALTER TABLE expenses ALTER COLUMN project TYPE projecttype USING project::projecttype;
ALTER TABLE news_generation_drafts ALTER COLUMN project TYPE projecttype USING project::projecttype;

-- Шаг 8: Добавляем ограничения  
ALTER TABLE users ADD CONSTRAINT chk_users_project_valid 
    CHECK (project IS NULL OR project IN ('gynecology.school', 'therapy.school', 'pediatrics.school', 'rusmedical'));

ALTER TABLE expenses ADD CONSTRAINT chk_expenses_project_valid 
    CHECK (project IN ('gynecology.school', 'therapy.school', 'pediatrics.school', 'rusmedical'));