-- Добавление роли ANALYST в enum userrole
-- Миграция: 09_add_analyst_role.sql

-- Добавляем новое значение в enum
ALTER TYPE userrole ADD VALUE 'ANALYST';