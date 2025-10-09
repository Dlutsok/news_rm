-- Migration 23: Add URL value to sourcetype enum
-- This migration adds 'URL' source type for articles parsed from external URLs

-- Add new enum value to sourcetype
-- Note: ALTER TYPE ADD VALUE cannot be run inside a transaction block in PostgreSQL
-- This migration should be run with autocommit=True

DO $$
BEGIN
    -- Check if the enum value already exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'URL'
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'sourcetype')
    ) THEN
        -- Add new enum value
        ALTER TYPE sourcetype ADD VALUE 'URL';
    END IF;
END$$;

-- Add comment
COMMENT ON TYPE sourcetype IS 'Типы источников новостей: RIA, MEDVESTNIK, AIG, REMEDIUM, RBC_MEDICAL, URL';
