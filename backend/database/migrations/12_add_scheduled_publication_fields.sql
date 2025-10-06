-- Добавляем поля для отложенной публикации новостей
-- scheduled_at: время запланированной публикации (UTC)
-- created_by: пользователь который создал черновик

ALTER TABLE news_generation_drafts
ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

ALTER TABLE news_generation_drafts
ADD COLUMN IF NOT EXISTS created_by INTEGER DEFAULT NULL;

-- Добавляем индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_news_generation_drafts_scheduled_at ON news_generation_drafts(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_news_generation_drafts_created_by ON news_generation_drafts(created_by);

-- Добавляем внешний ключ для created_by
ALTER TABLE news_generation_drafts
ADD CONSTRAINT fk_news_generation_drafts_created_by 
FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- Добавляем недостающие значения в enum newsstatus чтобы соответствовать данным в таблице
ALTER TYPE newsstatus ADD VALUE IF NOT EXISTS 'summary_pending';
ALTER TYPE newsstatus ADD VALUE IF NOT EXISTS 'summary_confirmed'; 
ALTER TYPE newsstatus ADD VALUE IF NOT EXISTS 'confirmed';
ALTER TYPE newsstatus ADD VALUE IF NOT EXISTS 'generated';
ALTER TYPE newsstatus ADD VALUE IF NOT EXISTS 'scheduled';
ALTER TYPE newsstatus ADD VALUE IF NOT EXISTS 'published';

-- Создаем enum если его нет (для новых установок)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'newsstatus') THEN
        CREATE TYPE newsstatus AS ENUM ('summary_pending', 'summary_confirmed', 'confirmed', 'generated', 'scheduled', 'published');
    END IF;
END
$$;

-- Конвертируем поле status в enum тип если это еще varchar
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'news_generation_drafts' 
        AND column_name = 'status' 
        AND data_type = 'character varying'
    ) THEN
        -- Конвертируем varchar в enum
        ALTER TABLE news_generation_drafts 
        ALTER COLUMN status TYPE newsstatus 
        USING status::newsstatus;
    END IF;
END
$$;

-- Комментарии для документации
COMMENT ON COLUMN news_generation_drafts.scheduled_at IS 'Время запланированной публикации в UTC';
COMMENT ON COLUMN news_generation_drafts.created_by IS 'ID пользователя который создал черновик';