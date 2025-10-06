-- =====================================================
-- МИГРАЦИЯ: Исправление constraint для колонки project
-- =====================================================

BEGIN;

-- Удаляем старое ограничение
ALTER TABLE expenses DROP CONSTRAINT IF EXISTS chk_expenses_project_valid;

-- Обновляем существующие данные с новыми значениями проектов
UPDATE expenses SET project = CASE
    WHEN project = 'GYNECOLOGY' THEN 'gynecology.school'
    WHEN project = 'THERAPY' THEN 'therapy.school'
    WHEN project = 'PEDIATRICS' THEN 'pediatrics.school'
    WHEN project = 'RUSMEDICAL' THEN 'rusmedical'
    ELSE project
END;

-- Добавляем новое ограничение с правильными значениями
ALTER TABLE expenses ADD CONSTRAINT chk_expenses_project_valid
CHECK (project IN ('gynecology.school', 'therapy.school', 'pediatrics.school', 'rusmedical'));

COMMIT;

-- Проверяем результат
SELECT 'Обновление constraint завершено. Новые значения проектов:' as message;
SELECT DISTINCT project FROM expenses ORDER BY project;