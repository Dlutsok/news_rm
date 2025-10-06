-- Исправление дублированных значений в enum newsstatus
-- Удаляем значения в ВЕРХНЕМ регистре, оставляем только нижний регистр

-- Создаем новый enum с правильными значениями
CREATE TYPE newsstatus_temp AS ENUM (
    'summary_pending', 
    'summary_confirmed', 
    'confirmed', 
    'generated', 
    'scheduled', 
    'published'
);

-- Временно изменяем колонку на text
ALTER TABLE news_generation_drafts ALTER COLUMN status TYPE text;

-- Удаляем старый enum
DROP TYPE newsstatus;

-- Переименовываем новый enum
ALTER TYPE newsstatus_temp RENAME TO newsstatus;

-- Возвращаем колонку обратно к enum типу
ALTER TABLE news_generation_drafts 
ALTER COLUMN status TYPE newsstatus 
USING status::newsstatus;

-- Комментарий
COMMENT ON TYPE newsstatus IS 'Статусы новостных черновиков (только в нижнем регистре)';