# План миграции структуры репозитория

## Фаза 1: Настройка алиасов (ЗАВЕРШЕНО ✅)

- ✅ Создан `jsconfig.json` с алиасами путей
- ✅ Обновлены импорты в frontend (66 файлов проанализировано, 20 обновлено)
- ✅ Созданы скрипты миграции
- ✅ Документирована текущая структура

## Фаза 2: Консолидация backend (ПЛАНИРУЕТСЯ)

### 2.1 Объединение моделей
```bash
# Перенос моделей из backend/models/ в backend/database/models/
./scripts/migration/mv_safe.sh backend/models backend/database/models

# Обновление импортов в коде
# Заменить: from models.* -> from database.models.*
```

### 2.2 Выделение AI компонентов
```bash
# Создание директории для AI
mkdir backend/ai

# Перенос AI-связанных сервисов
./scripts/migration/mv_safe.sh backend/services/openai_service.py backend/ai/
./scripts/migration/mv_safe.sh backend/services/yandex_service.py backend/ai/
```

### 2.3 Рефакторинг планировщиков
- Вынести планировщики из `main.py` в `backend/services/scheduler.py`
- Оставить в `main.py` только инициализацию FastAPI

## Фаза 3: Структурная оптимизация (БУДУЩЕЕ)

### 3.1 Frontend модули
```bash
# Создание дополнительных директорий
mkdir -p frontend/hooks
mkdir -p frontend/lib
mkdir -p frontend/constants
mkdir -p frontend/types

# Перенос утилит
./scripts/migration/mv_safe.sh frontend/utils frontend/lib
```

### 3.2 Мониторинг
```bash
# Создание модуля мониторинга
mkdir -p backend/monitoring

# Перенос мониторинг компонентов
./scripts/migration/mv_safe.sh backend/api/monitoring.py backend/monitoring/api.py
```

## Скрипты для автоматизации

### update_backend_imports.py (TODO)
```python
#!/usr/bin/env python3
"""Обновление импортов в backend после перемещения моделей"""

import os
import re
import sys

def update_imports(root_dir):
    """Обновить импорты в Python файлах"""
    patterns = [
        (r'from models\.', 'from database.models.'),
        (r'import models\.', 'import database.models.'),
    ]

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = os.path.join(dirpath, filename)
                update_file_imports(filepath, patterns)

def update_file_imports(filepath, patterns):
    """Обновить импорты в конкретном файле"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {filepath}")

    except Exception as e:
        print(f"Error updating {filepath}: {e}")

if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "backend"
    update_imports(root)
```

## Валидация после миграции

### Тестирование структуры
```bash
# Проверка что все импорты работают
cd frontend && npm run build

# Проверка backend
cd backend && python -m pytest tests/ -v

# Проверка что планировщики запускаются
cd backend && python main.py --check
```

### Структурные проверки
```bash
# Запуск CI проверок локально
.github/workflows/structure-check.yml

# Проверка что нет дублированных моделей
find backend -name "*.py" -exec grep -l "class.*Model" {} \; | sort

# Проверка что нет глубоких относительных импортов
find . -name "*.py" -o -name "*.js" | xargs grep -l "\.\./\.\./\.\."
```

## Откат изменений

В случае проблем:

```bash
# Откат через git
git revert <commit-hash>

# Или восстановление из backup
cp -r backup/backend/* backend/
cp -r backup/frontend/* frontend/

# Откат импортов
git checkout HEAD~1 -- frontend/jsconfig.json
node scripts/migration/restore_relative_imports.js
```

## Критерии успеха

- ✅ Все импорты работают корректно
- ✅ Нет дублирования кода/моделей
- ✅ CI проверки проходят
- ✅ Документация обновлена
- ✅ Команда понимает новую структуру

## Риски и митигация

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| Поломка импортов | Средняя | Пошаговая миграция, тесты после каждого шага |
| Конфликты при merge | Низкая | Координация с командой, feature branch |
| IDE не поддерживает алиасы | Низкая | jsconfig.json поддерживается везде |
| Потеря производительности | Очень низкая | Алиасы не влияют на runtime |