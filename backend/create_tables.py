#!/usr/bin/env python3
"""
Скрипт для создания таблиц базы данных
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import init_database, engine
from sqlmodel import Session, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_tables():
    """Проверка существования таблиц"""
    with Session(engine) as session:
        # Проверяем существование таблиц
        tables_to_check = ['bitrix_project_settings', 'app_settings']

        for table_name in tables_to_check:
            result = session.exec(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table_name}'
                );
            """)).first()

            if result:
                logger.info(f"✅ Таблица {table_name} существует")
            else:
                logger.warning(f"❌ Таблица {table_name} НЕ существует")

def main():
    """Основная функция"""
    try:
        logger.info("🔍 Проверка существования таблиц...")
        check_tables()

        logger.info("🚀 Создание таблиц...")
        init_database()

        logger.info("🔍 Повторная проверка таблиц...")
        check_tables()

        logger.info("✅ Готово!")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())