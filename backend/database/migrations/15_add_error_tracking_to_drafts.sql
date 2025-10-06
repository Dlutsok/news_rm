-- Migration 15: Add error tracking fields to news_generation_drafts table
-- This migration adds fields for tracking errors and enabling draft recovery

-- Add error tracking fields
ALTER TABLE news_generation_drafts
ADD COLUMN IF NOT EXISTS last_error_message TEXT;

ALTER TABLE news_generation_drafts
ADD COLUMN IF NOT EXISTS last_error_step VARCHAR(50);

ALTER TABLE news_generation_drafts
ADD COLUMN IF NOT EXISTS last_error_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE news_generation_drafts
ADD COLUMN IF NOT EXISTS can_retry BOOLEAN DEFAULT TRUE;

ALTER TABLE news_generation_drafts
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

-- Create indexes for better performance on error tracking queries
CREATE INDEX IF NOT EXISTS idx_news_generation_drafts_can_retry
ON news_generation_drafts(can_retry);

CREATE INDEX IF NOT EXISTS idx_news_generation_drafts_last_error_at
ON news_generation_drafts(last_error_at);

-- Update existing drafts to have default values for new fields
UPDATE news_generation_drafts
SET can_retry = TRUE, retry_count = 0
WHERE can_retry IS NULL OR retry_count IS NULL;

-- Add comments to explain the new fields
COMMENT ON COLUMN news_generation_drafts.last_error_message IS 'Последнее сообщение об ошибке';
COMMENT ON COLUMN news_generation_drafts.last_error_step IS 'Шаг процесса, на котором произошла ошибка (summary, generation, publication)';
COMMENT ON COLUMN news_generation_drafts.last_error_at IS 'Время последней ошибки';
COMMENT ON COLUMN news_generation_drafts.can_retry IS 'Можно ли повторить операцию с этим черновиком';
COMMENT ON COLUMN news_generation_drafts.retry_count IS 'Количество попыток восстановления';