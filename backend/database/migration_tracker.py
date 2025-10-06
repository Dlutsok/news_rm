#!/usr/bin/env python3
"""
Система отслеживания миграций базы данных
"""

from sqlmodel import create_engine, Session, text
from typing import List, Optional
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MigrationTracker:
    """Класс для отслеживания применённых миграций"""

    def __init__(self, engine):
        self.engine = engine
        self.ensure_migration_table()

    def ensure_migration_table(self):
        """Создать таблицу отслеживания миграций если её нет"""
        try:
            with Session(self.engine) as session:
                session.exec(text("""
                    CREATE TABLE IF NOT EXISTS migration_versions (
                        version_num VARCHAR(50) PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        filename VARCHAR(255) NOT NULL,
                        checksum VARCHAR(64),
                        execution_time INTEGER DEFAULT 0
                    );
                """))
                session.commit()
                logger.info("✅ Migration tracking table ensured")
        except Exception as e:
            logger.error(f"❌ Failed to create migration tracking table: {e}")
            raise

    def get_applied_migrations(self) -> List[str]:
        """Получить список применённых миграций"""
        try:
            with Session(self.engine) as session:
                result = session.exec(text(
                    "SELECT version_num FROM migration_versions ORDER BY version_num"
                ))
                applied = [row for row in result]
                logger.debug(f"Applied migrations: {applied}")
                return applied
        except Exception as e:
            logger.error(f"❌ Failed to get applied migrations: {e}")
            return []

    def mark_migration_applied(self, version: str, filename: str, execution_time: int = 0):
        """Отметить миграцию как применённую"""
        try:
            with Session(self.engine) as session:
                session.exec(text("""
                    INSERT INTO migration_versions (version_num, filename, execution_time)
                    VALUES (:version, :filename, :execution_time)
                    ON CONFLICT (version_num) DO UPDATE SET
                        applied_at = CURRENT_TIMESTAMP,
                        filename = :filename,
                        execution_time = :execution_time
                """), {
                    "version": version,
                    "filename": filename,
                    "execution_time": execution_time
                })
                session.commit()
                logger.info(f"✅ Marked migration {version} ({filename}) as applied")
        except Exception as e:
            logger.error(f"❌ Failed to mark migration {version} as applied: {e}")
            raise

    def get_pending_migrations(self, migrations_dir: Path) -> List[Path]:
        """Получить список неприменённых миграций"""
        try:
            applied = set(self.get_applied_migrations())

            if not migrations_dir.exists():
                logger.warning(f"Migrations directory does not exist: {migrations_dir}")
                return []

            # Получаем все SQL файлы и сортируем их
            all_migration_files = sorted(migrations_dir.glob("*.sql"))

            pending = []
            for migration_file in all_migration_files:
                # Извлекаем номер версии из имени файла (например, "01" из "01_create_users.sql")
                parts = migration_file.stem.split('_')
                if not parts:
                    continue

                version = parts[0]

                # Проверяем, что версия состоит из цифр
                if not version.isdigit():
                    logger.warning(f"Skipping file with invalid version format: {migration_file.name}")
                    continue

                if version not in applied:
                    pending.append(migration_file)
                    logger.debug(f"Pending migration: {migration_file.name}")

            logger.info(f"Found {len(pending)} pending migrations out of {len(all_migration_files)} total")
            return pending

        except Exception as e:
            logger.error(f"❌ Failed to get pending migrations: {e}")
            return []

    def get_migration_history(self) -> List[dict]:
        """Получить историю применённых миграций"""
        try:
            with Session(self.engine) as session:
                result = session.exec(text("""
                    SELECT version_num, filename, applied_at, execution_time
                    FROM migration_versions
                    ORDER BY applied_at DESC
                """))

                history = []
                for row in result:
                    history.append({
                        'version': row[0],
                        'filename': row[1],
                        'applied_at': row[2],
                        'execution_time': row[3]
                    })

                return history
        except Exception as e:
            logger.error(f"❌ Failed to get migration history: {e}")
            return []

    def is_migration_applied(self, version: str) -> bool:
        """Проверить, применена ли миграция"""
        applied_migrations = self.get_applied_migrations()
        return version in applied_migrations

    def validate_migration_sequence(self, migrations_dir: Path) -> bool:
        """Проверить корректность последовательности миграций"""
        try:
            if not migrations_dir.exists():
                return True

            all_migration_files = sorted(migrations_dir.glob("*.sql"))
            expected_version = 1

            for migration_file in all_migration_files:
                parts = migration_file.stem.split('_')
                if not parts or not parts[0].isdigit():
                    continue

                version = int(parts[0])
                if version != expected_version:
                    logger.error(f"❌ Migration sequence gap: expected {expected_version:02d}, found {version:02d}")
                    return False

                expected_version += 1

            logger.info("✅ Migration sequence is valid")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to validate migration sequence: {e}")
            return False