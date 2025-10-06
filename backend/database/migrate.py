#!/usr/bin/env python3
"""
Скрипт для миграций базы данных
"""

import sys
import os
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database.connection import init_database, engine
from database.migration_tracker import MigrationTracker
from services.auth_service import auth_service
from services.settings_service import settings_service
from sqlmodel import text, Session
import time


def run_sql_file(file_path: Path, tracker: MigrationTracker):
    """Выполнить SQL файл с отслеживанием версий"""
    if not file_path.exists():
        print(f"❌ SQL файл не найден: {file_path}")
        return False

    # Извлекаем версию из имени файла
    parts = file_path.stem.split('_')
    if not parts or not parts[0].isdigit():
        print(f"❌ Некорректный формат имени файла: {file_path.name}")
        print("   Ожидается формат: 01_description.sql")
        return False

    version = parts[0]

    # Проверяем, применена ли уже эта миграция
    if tracker.is_migration_applied(version):
        print(f"⏭️ Миграция {version} уже применена: {file_path.name}")
        return True

    try:
        start_time = time.time()

        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        with Session(engine) as session:
            # Разделяем на отдельные команды по ";"
            commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]

            for command in commands:
                if command:
                    session.exec(text(command))

            session.commit()

        execution_time = int((time.time() - start_time) * 1000)  # в миллисекундах

        # Отмечаем миграцию как применённую
        tracker.mark_migration_applied(version, file_path.name, execution_time)

        print(f"✅ SQL файл выполнен: {file_path.name} ({execution_time}ms)")
        return True

    except Exception as e:
        print(f"❌ Ошибка выполнения SQL файла {file_path.name}: {e}")
        return False


def run_migrations():
    """Запустить все миграции с отслеживанием версий"""
    print("🚀 Запуск миграций базы данных...")

    try:
        # Инициализируем трекер миграций
        tracker = MigrationTracker(engine)

        # Путь к папке с миграциями
        migrations_dir = Path(__file__).parent / "migrations"

        if not migrations_dir.exists():
            print(f"❌ Папка миграций не найдена: {migrations_dir}")
            return False

        # Проверяем корректность последовательности миграций
        if not tracker.validate_migration_sequence(migrations_dir):
            print("❌ Некорректная последовательность миграций")
            return False

        # Получаем список неприменённых миграций
        pending_migrations = tracker.get_pending_migrations(migrations_dir)

        if not pending_migrations:
            print("✅ Все миграции уже применены")
            return True

        print(f"📝 Найдено {len(pending_migrations)} неприменённых миграций")

        success_count = 0
        for migration_file in pending_migrations:
            print(f"🔄 Применение миграции: {migration_file.name}")
            if run_sql_file(migration_file, tracker):
                success_count += 1
            else:
                print(f"❌ Остановка на миграции: {migration_file.name}")
                break

        if success_count == len(pending_migrations):
            print(f"✅ Все миграции применены успешно: {success_count}/{len(pending_migrations)}")
            return True
        else:
            print(f"❌ Применено миграций: {success_count}/{len(pending_migrations)}")
            return False

    except Exception as e:
        print(f"❌ Ошибка запуска миграций: {e}")
        return False


def initialize_full_database():
    """Полная инициализация базы данных"""
    print("🔧 Полная инициализация базы данных...")
    
    try:
        # 1. Инициализируем базу через SQLModel
        print("1️⃣ Создание таблиц через SQLModel...")
        init_database()
        
        # 2. Запускаем миграции (если есть)
        print("2️⃣ Запуск миграций...")
        run_migrations()
        
        # 3. Инициализируем настройки по умолчанию
        print("3️⃣ Инициализация настроек...")
        settings_service.initialize_default_settings()
        
        # 4. Создаем администратора
        print("4️⃣ Создание администратора...")
        auth_service.initialize_admin()
        
        print("✅ База данных полностью инициализирована")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        return False


def show_migration_status():
    """Показать статус миграций"""
    try:
        tracker = MigrationTracker(engine)
        migrations_dir = Path(__file__).parent / "migrations"

        print("📊 Статус миграций:")
        print("=" * 50)

        # Показываем историю применённых миграций
        history = tracker.get_migration_history()
        if history:
            print("\n✅ Применённые миграции:")
            for migration in history:
                print(f"  {migration['version']} - {migration['filename']} ({migration['applied_at']})")

        # Показываем неприменённые миграции
        pending = tracker.get_pending_migrations(migrations_dir)
        if pending:
            print("\n⏳ Ожидающие применения:")
            for migration in pending:
                parts = migration.stem.split('_')
                version = parts[0] if parts and parts[0].isdigit() else "?"
                print(f"  {version} - {migration.name}")
        else:
            print("\n✅ Все миграции применены")

    except Exception as e:
        print(f"❌ Ошибка получения статуса миграций: {e}")


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python migrate.py init     - Полная инициализация БД")
        print("  python migrate.py migrate  - Запуск только миграций")
        print("  python migrate.py status   - Показать статус миграций")
        return

    command = sys.argv[1].lower()

    if command == "init":
        success = initialize_full_database()
    elif command == "migrate":
        success = run_migrations()
    elif command == "status":
        show_migration_status()
        success = True
    else:
        print(f"❌ Неизвестная команда: {command}")
        return

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()