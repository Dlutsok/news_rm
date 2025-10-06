-- Migration 16: Create telegram_posts table
-- This migration creates a table for storing Telegram posts related to published news

-- Create telegram_posts table
CREATE TABLE IF NOT EXISTS telegram_posts (
    id SERIAL PRIMARY KEY,
    news_draft_id INTEGER NOT NULL REFERENCES news_generation_drafts(id) ON DELETE CASCADE,

    -- Настройки генерации
    hook_type VARCHAR(50) NOT NULL DEFAULT 'question',
    disclosure_level VARCHAR(50) NOT NULL DEFAULT 'hint',
    call_to_action VARCHAR(50) NOT NULL DEFAULT 'curiosity',
    include_image BOOLEAN NOT NULL DEFAULT TRUE,

    -- Сгенерированный контент
    post_text TEXT NOT NULL,
    character_count INTEGER NOT NULL DEFAULT 0,

    -- Метаданные
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'Europe/Moscow'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'Europe/Moscow'),
    created_by INTEGER REFERENCES users(id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_telegram_posts_news_draft_id
ON telegram_posts(news_draft_id);

CREATE INDEX IF NOT EXISTS idx_telegram_posts_hook_type
ON telegram_posts(hook_type);

CREATE INDEX IF NOT EXISTS idx_telegram_posts_created_at
ON telegram_posts(created_at);

CREATE INDEX IF NOT EXISTS idx_telegram_posts_created_by
ON telegram_posts(created_by);

-- Add constraints for enum-like values
ALTER TABLE telegram_posts
ADD CONSTRAINT chk_telegram_posts_hook_type
CHECK (hook_type IN ('question', 'shocking_fact', 'statistics', 'contradiction'));

ALTER TABLE telegram_posts
ADD CONSTRAINT chk_telegram_posts_disclosure_level
CHECK (disclosure_level IN ('hint', 'main_idea', 'almost_all'));

ALTER TABLE telegram_posts
ADD CONSTRAINT chk_telegram_posts_call_to_action
CHECK (call_to_action IN ('curiosity', 'urgency', 'expertise'));

-- Add comments to explain the table structure
COMMENT ON TABLE telegram_posts IS 'Telegram посты для опубликованных новостей';
COMMENT ON COLUMN telegram_posts.news_draft_id IS 'ID связанной новости из news_generation_drafts';
COMMENT ON COLUMN telegram_posts.hook_type IS 'Тип зацепки (question, shocking_fact, statistics, contradiction)';
COMMENT ON COLUMN telegram_posts.disclosure_level IS 'Уровень раскрытия информации (hint, main_idea, almost_all)';
COMMENT ON COLUMN telegram_posts.call_to_action IS 'Тип призыва к действию (curiosity, urgency, expertise)';
COMMENT ON COLUMN telegram_posts.include_image IS 'Прикреплять ли изображение из статьи';
COMMENT ON COLUMN telegram_posts.post_text IS 'Текст сгенерированного поста';
COMMENT ON COLUMN telegram_posts.character_count IS 'Количество символов в тексте поста';
COMMENT ON COLUMN telegram_posts.created_at IS 'Время создания поста';
COMMENT ON COLUMN telegram_posts.updated_at IS 'Время последнего обновления';
COMMENT ON COLUMN telegram_posts.created_by IS 'ID пользователя, создавшего пост';