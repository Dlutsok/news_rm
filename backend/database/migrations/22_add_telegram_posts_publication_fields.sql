-- Migration 22: Add publication tracking fields to telegram_posts
-- This migration adds fields for tracking Telegram post publication status

-- Add publication tracking fields
ALTER TABLE telegram_posts
ADD COLUMN IF NOT EXISTS is_published BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE telegram_posts
ADD COLUMN IF NOT EXISTS published_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE telegram_posts
ADD COLUMN IF NOT EXISTS telegram_message_id INTEGER;

-- Create indexes for new fields
CREATE INDEX IF NOT EXISTS idx_telegram_posts_is_published
ON telegram_posts(is_published);

CREATE INDEX IF NOT EXISTS idx_telegram_posts_published_at
ON telegram_posts(published_at);

-- Add comments
COMMENT ON COLUMN telegram_posts.is_published IS 'Опубликован ли пост в Telegram';
COMMENT ON COLUMN telegram_posts.published_at IS 'Время публикации в Telegram';
COMMENT ON COLUMN telegram_posts.telegram_message_id IS 'ID сообщения в Telegram';
