-- Создание таблицы расходов (expenses)
-- Таблица для отслеживания затрат пользователей на различные операции в системе

CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project VARCHAR(50) NOT NULL,
    expense_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    description TEXT,
    related_article_id INTEGER REFERENCES articles(id) ON DELETE SET NULL,
    related_session_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Создание индексов для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_expenses_user_id ON expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_project ON expenses(project);
CREATE INDEX IF NOT EXISTS idx_expenses_expense_type ON expenses(expense_type);
CREATE INDEX IF NOT EXISTS idx_expenses_amount ON expenses(amount);
CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses(created_at);
CREATE INDEX IF NOT EXISTS idx_expenses_user_project ON expenses(user_id, project);
CREATE INDEX IF NOT EXISTS idx_expenses_user_type ON expenses(user_id, expense_type);
CREATE INDEX IF NOT EXISTS idx_expenses_project_type ON expenses(project, expense_type);

-- Добавление ограничений
ALTER TABLE expenses ADD CONSTRAINT chk_expenses_amount_positive CHECK (amount > 0);
ALTER TABLE expenses ADD CONSTRAINT chk_expenses_project_valid 
    CHECK (project IN ('gynecology.school', 'therapy.school', 'pediatrics.school', 'rusmedical'));
ALTER TABLE expenses ADD CONSTRAINT chk_expenses_type_valid 
    CHECK (expense_type IN ('news_creation', 'photo_regeneration', 'gpt_message'));

-- Комментарии к таблице
COMMENT ON TABLE expenses IS 'Таблица расходов пользователей на операции в системе';
COMMENT ON COLUMN expenses.id IS 'Уникальный идентификатор расхода';
COMMENT ON COLUMN expenses.user_id IS 'ID пользователя, совершившего операцию';
COMMENT ON COLUMN expenses.project IS 'Проект, к которому относится расход';
COMMENT ON COLUMN expenses.expense_type IS 'Тип расхода: news_creation, photo_regeneration, gpt_message';
COMMENT ON COLUMN expenses.amount IS 'Сумма расхода в рублях';
COMMENT ON COLUMN expenses.description IS 'Описание операции';
COMMENT ON COLUMN expenses.related_article_id IS 'ID связанной статьи (для новостей и фото)';
COMMENT ON COLUMN expenses.related_session_id IS 'ID сессии для операций GPT';
COMMENT ON COLUMN expenses.created_at IS 'Дата создания записи о расходе';
COMMENT ON COLUMN expenses.updated_at IS 'Дата последнего обновления записи';

-- Создание функции для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_expenses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создание триггера для автоматического обновления updated_at
CREATE TRIGGER update_expenses_updated_at_trigger
    BEFORE UPDATE ON expenses
    FOR EACH ROW
    EXECUTE FUNCTION update_expenses_updated_at();