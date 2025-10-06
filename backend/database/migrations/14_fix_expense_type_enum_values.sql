-- =====================================================
-- МИГРАЦИЯ: Исправление значений enum ExpenseType
-- =====================================================
-- Цель: Привести значения enum к единому формату (нижний регистр)
-- Безопасно для продакшена: проверяет существование данных

BEGIN;

-- Проверяем, существует ли таблица expenses
DO $$
BEGIN
    -- Проверяем существование таблицы expenses
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'expenses') THEN
        RAISE NOTICE 'Таблица expenses не существует, пропускаем миграцию';
        RETURN;
    END IF;

    -- Проверяем существование типа expensetype
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'expensetype') THEN
        RAISE NOTICE 'Тип expensetype не существует, создаем с правильными значениями';
        CREATE TYPE expensetype AS ENUM (
            'news_creation',
            'photo_regeneration',
            'gpt_message'
        );
        RETURN;
    END IF;

    -- Получаем текущие значения enum
    IF EXISTS (
        SELECT 1 FROM pg_enum pe
        JOIN pg_type pt ON pe.enumtypid = pt.oid
        WHERE pt.typname = 'expensetype'
        AND pe.enumlabel IN ('NEWS_CREATION', 'PHOTO_REGENERATION', 'GPT_MESSAGE')
    ) THEN
        RAISE NOTICE 'Найдены значения в верхнем регистре, выполняем конвертацию';

        -- Создаем новый тип enum с правильными значениями
        CREATE TYPE expensetype_new AS ENUM (
            'news_creation',
            'photo_regeneration',
            'gpt_message'
        );

        -- Обновляем существующие данные в таблице expenses
        UPDATE expenses SET expense_type = CASE
            WHEN expense_type::text = 'NEWS_CREATION' THEN 'news_creation'
            WHEN expense_type::text = 'PHOTO_REGENERATION' THEN 'photo_regeneration'
            WHEN expense_type::text = 'GPT_MESSAGE' THEN 'gpt_message'
            ELSE expense_type::text
        END::expensetype_new;

        -- Меняем тип колонки на новый enum
        ALTER TABLE expenses ALTER COLUMN expense_type TYPE expensetype_new
        USING expense_type::text::expensetype_new;

        -- Удаляем старый enum
        DROP TYPE expensetype;

        -- Переименовываем новый enum
        ALTER TYPE expensetype_new RENAME TO expensetype;

        RAISE NOTICE 'Миграция ExpenseType завершена успешно';

    ELSIF EXISTS (
        SELECT 1 FROM pg_enum pe
        JOIN pg_type pt ON pe.enumtypid = pt.oid
        WHERE pt.typname = 'expensetype'
        AND pe.enumlabel IN ('news_creation', 'photo_regeneration', 'gpt_message')
    ) THEN
        RAISE NOTICE 'Значения ExpenseType уже в правильном формате, миграция не требуется';

    ELSE
        RAISE NOTICE 'Неизвестные значения в ExpenseType, добавляем недостающие';

        -- Добавляем недостающие значения если их нет
        DO $enum$
        BEGIN
            IF NOT EXISTS(SELECT 1 FROM pg_enum pe JOIN pg_type pt ON pe.enumtypid = pt.oid WHERE pt.typname = 'expensetype' AND pe.enumlabel = 'news_creation') THEN
                ALTER TYPE expensetype ADD VALUE IF NOT EXISTS 'news_creation';
            END IF;
            IF NOT EXISTS(SELECT 1 FROM pg_enum pe JOIN pg_type pt ON pe.enumtypid = pt.oid WHERE pt.typname = 'expensetype' AND pe.enumlabel = 'photo_regeneration') THEN
                ALTER TYPE expensetype ADD VALUE IF NOT EXISTS 'photo_regeneration';
            END IF;
            IF NOT EXISTS(SELECT 1 FROM pg_enum pe JOIN pg_type pt ON pe.enumtypid = pt.oid WHERE pt.typname = 'expensetype' AND pe.enumlabel = 'gpt_message') THEN
                ALTER TYPE expensetype ADD VALUE IF NOT EXISTS 'gpt_message';
            END IF;
        END $enum$;
    END IF;
END $$;

COMMIT;

-- Проверяем результат миграции
DO $$
DECLARE
    enum_values text;
BEGIN
    SELECT string_agg(pe.enumlabel, ', ' ORDER BY pe.enumsortorder) INTO enum_values
    FROM pg_enum pe
    JOIN pg_type pt ON pe.enumtypid = pt.oid
    WHERE pt.typname = 'expensetype';

    RAISE NOTICE 'Текущие значения ExpenseType: %', enum_values;
END $$;