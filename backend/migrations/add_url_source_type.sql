-- Миграция: добавление типа источника URL
-- Дата: 2025-01-06
-- Описание: Добавляет новый тип источника 'URL' для статей, загруженных по URL

-- Для PostgreSQL нужно добавить новое значение в enum (в верхнем регистре, как и остальные значения)
ALTER TYPE sourcetype ADD VALUE IF NOT EXISTS 'URL';

-- Комментарий для документации
COMMENT ON TYPE sourcetype IS 'Типы источников новостей: RIA, MEDVESTNIK, AIG, REMEDIUM, RBC_MEDICAL, URL';
