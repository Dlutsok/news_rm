#!/bin/bash

# =====================================================
# СКРИПТ ПРИМЕНЕНИЯ МИГРАЦИИ 14 НА ПРОДАКШЕНЕ
# =====================================================

set -e  # Остановить выполнение при ошибке

echo "=========================================="
echo "Применение миграции 14: ExpenseType enum"
echo "=========================================="

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

# Создаем резервную копию (опционально)
echo "📦 Создание резервной копии enum значений..."
psql "$DATABASE_URL" -c "
CREATE TABLE IF NOT EXISTS migration_backup_14 AS
SELECT 'Before migration' as note, expense_type::text, count(*)
FROM expenses
GROUP BY expense_type::text;
" || echo "⚠️ Предупреждение: Не удалось создать резервную копию"

# Показываем текущее состояние
echo "📊 Текущие значения ExpenseType в БД:"
psql "$DATABASE_URL" -c "
SELECT pe.enumlabel as enum_value, COUNT(e.id) as usage_count
FROM pg_enum pe
JOIN pg_type pt ON pe.enumtypid = pt.oid
LEFT JOIN expenses e ON e.expense_type::text = pe.enumlabel
WHERE pt.typname = 'expensetype'
GROUP BY pe.enumlabel, pe.enumsortorder
ORDER BY pe.enumsortorder;
" 2>/dev/null || echo "ℹ️ Таблица expenses пока не существует"

# Применяем миграцию
echo "🚀 Применение миграции..."
psql "$DATABASE_URL" -f "$(dirname "$0")/14_fix_expense_type_enum_values.sql"

if [ $? -eq 0 ]; then
    echo "✅ Миграция применена успешно!"

    # Показываем результат
    echo "📊 Результат миграции:"
    psql "$DATABASE_URL" -c "
    SELECT pe.enumlabel as enum_value, COUNT(e.id) as usage_count
    FROM pg_enum pe
    JOIN pg_type pt ON pe.enumtypid = pt.oid
    LEFT JOIN expenses e ON e.expense_type::text = pe.enumlabel
    WHERE pt.typname = 'expensetype'
    GROUP BY pe.enumlabel, pe.enumsortorder
    ORDER BY pe.enumsortorder;
    " 2>/dev/null || echo "ℹ️ Enum создан, данных пока нет"

    echo "🎉 Миграция завершена!"
else
    echo "❌ Ошибка при применении миграции"
    exit 1
fi

echo "=========================================="
echo "Готово! Теперь можно запускать обновленный код"
echo "=========================================="