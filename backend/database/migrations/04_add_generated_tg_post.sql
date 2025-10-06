-- Добавляем колонку generated_tg_post для хранения текста анонса Telegram
ALTER TABLE news_generation_drafts
ADD COLUMN IF NOT EXISTS generated_tg_post TEXT;


