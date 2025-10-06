-- Migration 17: Create publications table for multiple article publications
-- This enables one article to be published to multiple projects

-- Create table only if it doesn't exist
CREATE TABLE IF NOT EXISTS publications (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    project_code VARCHAR(10) NOT NULL,
    project_name VARCHAR(100),
    bitrix_id INTEGER NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    published_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Unique constraint: one article can be published to one project only once
    CONSTRAINT uk_publications_article_project UNIQUE (article_id, project_code)
);

-- Create indexes (only if they don't exist)
CREATE INDEX IF NOT EXISTS idx_publications_article_id ON publications(article_id);
CREATE INDEX IF NOT EXISTS idx_publications_project_code ON publications(project_code);
CREATE INDEX IF NOT EXISTS idx_publications_published_at ON publications(published_at);
CREATE INDEX IF NOT EXISTS idx_publications_published_by ON publications(published_by);

-- Add comment to table
COMMENT ON TABLE publications IS 'Stores publications of articles to different projects (many-to-many relationship)';
COMMENT ON COLUMN publications.article_id IS 'Reference to the published article';
COMMENT ON COLUMN publications.project_code IS 'Project code (GS, TS, PS, TEST, etc.)';
COMMENT ON COLUMN publications.project_name IS 'Human-readable project name';
COMMENT ON COLUMN publications.bitrix_id IS 'ID of the published article in Bitrix CMS';
COMMENT ON COLUMN publications.published_at IS 'When the article was published to this project';
COMMENT ON COLUMN publications.published_by IS 'User who published the article';