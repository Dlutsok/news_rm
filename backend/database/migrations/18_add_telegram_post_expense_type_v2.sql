-- =====================================================
-- МИГРАЦИЯ: Добавление нового типа расхода telegram_post
-- =====================================================

BEGIN;

-- Сначала исправляем существующие значения на правильные (нижний регистр)
-- и добавляем новый тип telegram_post

-- Создаем новый тип enum с правильными значениями
CREATE TYPE expensetype_fixed AS ENUM (
    'news_creation',
    'photo_regeneration',
    'gpt_message',
    'telegram_post'
);

-- Добавляем новую колонку с правильным типом
ALTER TABLE expenses ADD COLUMN expense_type_new expensetype_fixed;

-- Переносим данные с конвертацией
UPDATE expenses SET expense_type_new = CASE
    WHEN expense_type::text = 'NEWS_CREATION' THEN 'news_creation'::expensetype_fixed
    WHEN expense_type::text = 'PHOTO_REGENERATION' THEN 'photo_regeneration'::expensetype_fixed
    WHEN expense_type::text = 'GPT_MESSAGE' THEN 'gpt_message'::expensetype_fixed
    ELSE 'gpt_message'::expensetype_fixed  -- fallback для неизвестных значений
END;

-- Удаляем старую колонку
ALTER TABLE expenses DROP COLUMN expense_type;

-- Переименовываем новую колонку
ALTER TABLE expenses RENAME COLUMN expense_type_new TO expense_type;

-- Удаляем старый тип
DROP TYPE expensetype;

-- Переименовываем новый тип
ALTER TYPE expensetype_fixed RENAME TO expensetype;

COMMIT;

-- Проверяем результат
SELECT 'Миграция завершена. Новые значения ExpenseType:' as message;
SELECT enumlabel FROM pg_enum pe
JOIN pg_type pt ON pe.enumtypid = pt.oid
WHERE pt.typname = 'expensetype'
ORDER BY pe.enumsortorder;