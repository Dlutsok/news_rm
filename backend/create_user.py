#!/usr/bin/env python3
"""
Скрипт для проверки и создания пользователей
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import engine
from database.models import User, UserRole, ProjectType
from services.auth_service import AuthService
from sqlmodel import Session, select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_users():
    """Проверка существующих пользователей"""
    with Session(engine) as session:
        stmt = select(User)
        users = session.exec(stmt).all()

        logger.info(f"Найдено пользователей: {len(users)}")
        for user in users:
            logger.info(f"  - {user.username} ({user.role}) - проект: {user.project}")

        return len(users)

def create_admin_user():
    """Создание админа"""
    with Session(engine) as session:
        # Проверяем, существует ли уже admin
        stmt = select(User).where(User.username == "admin")
        existing_user = session.exec(stmt).first()

        if existing_user:
            logger.info("Пользователь 'admin' уже существует")
            return existing_user

        # Создаем админа
        hashed_password = AuthService.get_password_hash("admin123")
        admin_user = User(
            username="admin",
            role=UserRole.ADMIN,
            hashed_password=hashed_password,
            project=ProjectType.GYNECOLOGY  # По умолчанию
        )

        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)

        logger.info("✅ Создан пользователь 'admin' с паролем 'admin123'")
        return admin_user

def create_test_token():
    """Создание тестового токена"""
    token = AuthService.create_access_token(data={"sub": "admin"})
    logger.info(f"🔑 Тестовый токен для пользователя 'admin':")
    logger.info(f"Bearer {token}")
    return token

def main():
    """Основная функция"""
    try:
        logger.info("🔍 Проверка пользователей...")
        user_count = check_users()

        if user_count == 0:
            logger.info("👤 Создание админа...")
            create_admin_user()

        logger.info("🔑 Генерация тестового токена...")
        create_test_token()

        logger.info("✅ Готово!")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())