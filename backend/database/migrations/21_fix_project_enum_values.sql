-- Исправление значений enum в базе данных для совместимости с SQLModel
-- Обновляем существующие значения проектов на правильные enum значения

-- Сначала удаляем ограничение
ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_users_project_valid;

-- Обновляем значения на правильные enum значения
UPDATE users SET project = 'GYNECOLOGY' WHERE project = 'gynecology.school';
UPDATE users SET project = 'THERAPY' WHERE project = 'therapy.school';  
UPDATE users SET project = 'PEDIATRICS' WHERE project = 'pediatrics.school';
UPDATE users SET project = 'RUSMEDICAL' WHERE project = 'rusmedical';

-- Создаем новое ограничение с правильными enum значениями
ALTER TABLE users ADD CONSTRAINT chk_users_project_valid 
    CHECK (project IS NULL OR project IN ('GYNECOLOGY', 'THERAPY', 'PEDIATRICS', 'RUSMEDICAL'));

-- Обновляем комментарий
COMMENT ON COLUMN users.project IS 'Привязка пользователя к проекту для автоматического учета расходов (enum значения)';

-- Аналогично для таблицы expenses
ALTER TABLE expenses DROP CONSTRAINT IF EXISTS chk_expenses_project_valid;

UPDATE expenses SET project = 'GYNECOLOGY' WHERE project = 'gynecology.school';
UPDATE expenses SET project = 'THERAPY' WHERE project = 'therapy.school';
UPDATE expenses SET project = 'PEDIATRICS' WHERE project = 'pediatrics.school'; 
UPDATE expenses SET project = 'RUSMEDICAL' WHERE project = 'rusmedical';

ALTER TABLE expenses ADD CONSTRAINT chk_expenses_project_valid 
    CHECK (project IN ('GYNECOLOGY', 'THERAPY', 'PEDIATRICS', 'RUSMEDICAL'));