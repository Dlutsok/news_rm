-- Create table publication_logs for analytics of site publications
CREATE TABLE IF NOT EXISTS publication_logs (
    id SERIAL PRIMARY KEY,
    draft_id INTEGER,
    username VARCHAR(100),
    project VARCHAR(200),
    bitrix_id INTEGER,
    url VARCHAR(1000),
    image_url VARCHAR(1000),
    seo_title VARCHAR(300),
    cost_rub INTEGER DEFAULT 0,
    published_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Indexes for faster analytics queries
CREATE INDEX IF NOT EXISTS idx_publication_logs_published_at ON publication_logs(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_publication_logs_username ON publication_logs(username);
CREATE INDEX IF NOT EXISTS idx_publication_logs_project ON publication_logs(project);
CREATE INDEX IF NOT EXISTS idx_publication_logs_draft_id ON publication_logs(draft_id);

