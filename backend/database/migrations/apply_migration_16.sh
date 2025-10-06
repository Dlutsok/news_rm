#!/bin/bash

# =====================================================
# СКРИПТ ПРИМЕНЕНИЯ МИГРАЦИИ 16 НА ПРОДАКШЕНЕ
# =====================================================

set -e  # Остановить выполнение при ошибке

echo "=============================================="
echo "Применение миграции 16: telegram_posts table"
echo "=============================================="

# Проверяем наличие переменной DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Ошибка: Переменная DATABASE_URL не задана"
    echo "Пример: export DATABASE_URL='postgresql://user:password@localhost:5432/dbname'"
    exit 1
fi

echo "🔍 Подключение к базе данных..."
echo "URL: $(echo $DATABASE_URL | sed 's/:[^:]*@/:***@/')"  # Скрываем пароль в выводе

# Проверяем подключение к БД
if ! psql "$DATABASE_URL" -c "SELECT version();" > /dev/null 2>&1; then
    echo "❌ Ошибка: Не удается подключиться к базе данных"
    exit 1
fi

echo "✅ Подключение успешно"

# Проверяем, не существует ли уже таблица
echo "🔍 Проверка существования таблицы telegram_posts..."
TABLE_EXISTS=$(psql "$DATABASE_URL" -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'telegram_posts');" | xargs)

if [ "$TABLE_EXISTS" = "t" ]; then
    echo "⚠️ Таблица telegram_posts уже существует. Пропускаем миграцию."
    echo "📊 Текущая структура таблицы:"
    psql "$DATABASE_URL" -c "\d telegram_posts"
    exit 0
fi

# Показываем связанные таблицы
echo "📊 Проверка связанных таблиц (news_generation_drafts, users):"
psql "$DATABASE_URL" -c "SELECT COUNT(*) as news_drafts_count FROM news_generation_drafts;" 2>/dev/null || echo "ℹ️ Таблица news_generation_drafts не найдена"
psql "$DATABASE_URL" -c "SELECT COUNT(*) as users_count FROM users;" 2>/dev/null || echo "ℹ️ Таблица users не найдена"

# Применяем миграцию
echo "🚀 Применение миграции..."
psql "$DATABASE_URL" -f "$(dirname "$0")/16_create_telegram_posts_table.sql"

if [ $? -eq 0 ]; then
    echo "✅ Миграция применена успешно!"

    # Показываем результат
    echo "📊 Структура новой таблицы:"
    psql "$DATABASE_URL" -c "\d telegram_posts"

    echo "📊 Проверка индексов:"
    psql "$DATABASE_URL" -c "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'telegram_posts';"

    echo "🎉 Миграция завершена!"
else
    echo "❌ Ошибка при применении миграции"
    exit 1
fi

echo "=============================================="
echo "Готово! Таблица telegram_posts создана и готова к использованию"
echo "Теперь можно создавать Telegram посты для опубликованных новостей"
echo "=============================================="