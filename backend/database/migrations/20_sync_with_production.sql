-- Синхронизация локальных моделей с production БД
-- Дата: 22 сентября 2025
-- Описание: Обеспечение совместимости ENUM значений

BEGIN;

-- Проверяем и добавляем недостающее значение в projecttype если его нет
DO $$
BEGIN
    -- Добавляем rusmedical если его нет
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'projecttype' AND e.enumlabel = 'rusmedical'
    ) THEN
        ALTER TYPE projecttype ADD VALUE 'rusmedical';
        RAISE NOTICE 'Добавлено значение rusmedical в projecttype';
    ELSE
        RAISE NOTICE 'Значение rusmedical уже существует в projecttype';
    END IF;
END$$;

-- Проверяем соответствие ENUM значений с кодом
-- Это комментарий для документации ожидаемых значений:
-- SourceType: 'ria', 'medvestnik', 'aig', 'remedium', 'rbc_medical' (lowercase для совместимости с frontend)
-- UserRole: 'admin', 'staff', 'analyst' (lowercase для совместимости с frontend)
-- ProjectType: 'gynecology.school', 'therapy.school', 'pediatrics.school', 'rusmedical'

-- ВАЖНО: Если в production БД используются uppercase значения (RIA, ADMIN и т.д.),
-- а код ожидает lowercase, то необходимо либо:
-- 1. Обновить значения в БД на lowercase
-- 2. Или обновить код для работы с uppercase

COMMIT;
