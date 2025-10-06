#!/usr/bin/env python3
"""
Скрипт для исправления роли администратора
"""

import sys
import os
from pathlib import Path

# Добавляем backend в путь
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from database.connection import engine
from database.models import User, UserRole
from services.auth_service import AuthService
from sqlmodel import Session, select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_current_admin():
    """Проверить текущего админа"""
    with Session(engine) as session:
        # Ищем админа
        stmt = select(User).where(User.username == "admin")
        admin_user = session.exec(stmt).first()
        
        if admin_user:
            logger.info(f"👤 Пользователь 'admin' найден:")
            logger.info(f"   - Роль: {admin_user.role}")
            logger.info(f"   - Проект: {admin_user.project}")
            logger.info(f"   - ID: {admin_user.id}")
            return admin_user
        else:
            logger.warning("❌ Пользователь 'admin' не найден!")
            return None

def fix_admin_role():
    """Исправить роль администратора"""
    with Session(engine) as session:
        # Находим админа
        stmt = select(User).where(User.username == "admin")
        admin_user = session.exec(stmt).first()
        
        if not admin_user:
            logger.error("❌ Пользователь 'admin' не найден!")
            
            # Создаем админа
            logger.info("🔧 Создаем нового администратора...")
            hashed_password = AuthService.get_password_hash("admin123")
            
            new_admin = User(
                username="admin",
                role=UserRole.ADMIN,  # Это теперь "admin" (lowercase)
                hashed_password=hashed_password
            )
            
            session.add(new_admin)
            session.commit()
            session.refresh(new_admin)
            
            logger.info("✅ Создан новый администратор:")
            logger.info(f"   - Логин: admin")
            logger.info(f"   - Пароль: admin123")
            logger.info(f"   - Роль: {new_admin.role}")
            
            return new_admin
        
        # Проверяем и исправляем роль
        if admin_user.role != UserRole.ADMIN:
            logger.info(f"🔧 Исправляем роль с '{admin_user.role}' на '{UserRole.ADMIN}'")
            
            admin_user.role = UserRole.ADMIN
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            
            logger.info("✅ Роль администратора исправлена!")
        else:
            logger.info("✅ Роль администратора уже корректна")
        
        return admin_user

def check_all_users():
    """Показать всех пользователей"""
    with Session(engine) as session:
        stmt = select(User)
        users = session.exec(stmt).all()
        
        logger.info("📋 Все пользователи в системе:")
        for user in users:
            logger.info(f"   - {user.username} | {user.role} | проект: {user.project}")

def main():
    """Основная функция"""
    try:
        logger.info("🔍 Проверка текущего состояния админа...")
        check_current_admin()
        
        logger.info("\n🔧 Исправление роли администратора...")
        admin_user = fix_admin_role()
        
        logger.info("\n📋 Проверка результата...")
        check_current_admin()
        
        logger.info("\n👥 Все пользователи:")
        check_all_users()
        
        logger.info("\n✅ Готово! Теперь админу должны быть доступны все 3 вкладки:")
        logger.info("   1. Настройки (/settings)")
        logger.info("   2. Мониторинг расходов (/expenses)") 
        logger.info("   3. Мониторинг системы (/system-monitoring)")
        
        logger.info("\n🔑 Данные для входа:")
        logger.info("   Логин: admin")
        logger.info("   Пароль: admin123")
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
