#!/bin/bash
set -e

echo "🚀 Starting Medical News Backend..."

# Получаем хост и порт БД из переменных окружения или используем дефолтные значения
DB_HOST=${DATABASE_HOST:-172.18.0.1}
DB_PORT=${DATABASE_PORT:-5432}
DB_USER=${DATABASE_USER:-postgres}

echo "📡 Database connection info:"
echo "   Host: ${DB_HOST}"
echo "   Port: ${DB_PORT}"
echo "   User: ${DB_USER}"

# Ждём готовности PostgreSQL
echo "⏳ Waiting for PostgreSQL to be ready..."
/wait-for-db.sh "${DB_HOST}:${DB_PORT}" --timeout=60

echo "✅ PostgreSQL is ready!"

# Применяем миграции автоматически
echo "🔄 Applying database migrations..."
cd /app

# Проверяем доступность скрипта миграций
if [ -f "database/migrate.py" ]; then
    echo "📄 Running database migrations..."
    python database/migrate.py init
    echo "✅ Database migrations completed successfully"
else
    echo "⚠️ Migration script not found, skipping migrations"
fi

# Проверяем успешность подключения к БД
echo "🔍 Testing database connection..."
python -c "
from database.connection import engine
from sqlmodel import Session, text
try:
    with Session(engine) as session:
        result = session.exec(text('SELECT version();')).first()
        print(f'✅ Database connected successfully: {result}')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

echo "🎯 Database setup completed!"

# Запускаем приложение
echo "🚀 Starting FastAPI server..."
echo "🌐 Server will be available at: http://0.0.0.0:8000"
echo "📊 Health check endpoint: http://0.0.0.0:8000/health"
echo "📖 API documentation: http://0.0.0.0:8000/docs"

exec "$@"