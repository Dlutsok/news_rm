# Миграция 14: Исправление ExpenseType enum

## Проблема
- В коде используются значения enum в нижнем регистре: `photo_regeneration`
- В базе данных enum содержит значения в верхнем регистре: `PHOTO_REGENERATION`
- Это вызывает ошибку: `invalid input value for enum expensetype: "photo_regeneration"`

## Решение
Миграция приводит значения enum к единому формату (нижний регистр) и безопасно обновляет существующие данные.

## Файлы миграции
- `14_fix_expense_type_enum_values.sql` - основная миграция
- `apply_migration_14.sh` - скрипт для применения на продакшене
- `README_migration_14.md` - эта инструкция

## Применение на продакшене

### Вариант 1: Автоматический скрипт (рекомендуется)
```bash
# Установите переменную DATABASE_URL
export DATABASE_URL='postgresql://user:password@host:port/database'

# Запустите скрипт
cd backend/database/migrations
./apply_migration_14.sh
```

### Вариант 2: Ручное применение
```bash
# Подключитесь к базе данных
psql "postgresql://user:password@host:port/database"

# Выполните миграцию
\i 14_fix_expense_type_enum_values.sql
```

## Что делает миграция

1. **Проверяет существование** таблицы `expenses` и типа `expensetype`
2. **Определяет текущий формат** значений enum
3. **Выполняет конвертацию** если нужно:
   - `NEWS_CREATION` → `news_creation`
   - `PHOTO_REGENERATION` → `photo_regeneration`
   - `GPT_MESSAGE` → `gpt_message`
4. **Обновляет существующие данные** в таблице
5. **Создает резервную копию** значений (в скрипте)

## Безопасность

- ✅ Проверяет существование всех объектов перед изменением
- ✅ Использует транзакции для атомарности
- ✅ Создает резервную копию данных
- ✅ Показывает подробные логи выполнения
- ✅ Можно запускать повторно (идемпотентная)

## После применения

1. **Перезапустите backend** для применения изменений в коде
2. **Проверьте логи**, что ошибки `invalid input value for enum` исчезли
3. **Протестируйте** создание новостей и перегенерацию изображений

## Откат (если нужно)

Если что-то пошло не так, можно восстановить из резервной копии:
```sql
-- Посмотреть резервную копию
SELECT * FROM migration_backup_14;

-- При необходимости вернуть старые значения
-- (требует создания enum с старыми значениями)
```

## Проверка результата

```sql
-- Посмотреть текущие значения enum
SELECT enumlabel FROM pg_enum pe
JOIN pg_type pt ON pe.enumtypid = pt.oid
WHERE pt.typname = 'expensetype'
ORDER BY pe.enumsortorder;

-- Посмотреть использование в таблице
SELECT expense_type, count(*) FROM expenses GROUP BY expense_type;
```