#!/usr/bin/env python3
"""
Скрипт для сброса пароля пользователя admin
"""

from database.connection import engine
from sqlmodel import Session, select
from database.models import User
from services.auth_service import AuthService

def reset_admin_password():
    """Сбросить пароль пользователя admin на 'admin'"""

    with Session(engine) as session:
        # Находим пользователя admin
        statement = select(User).where(User.username == "admin")
        admin_user = session.exec(statement).first()

        if not admin_user:
            print("❌ Пользователь 'admin' не найден в базе данных!")
            print("Доступные пользователи:")
            all_users = session.exec(select(User)).all()
            for user in all_users:
                print(f"  - {user.username} (role: {user.role})")
            return

        # Сбрасываем пароль на 'admin'
        new_password = "admin"
        admin_user.hashed_password = AuthService.get_password_hash(new_password)

        session.add(admin_user)
        session.commit()

        print(f"✅ Пароль для пользователя '{admin_user.username}' успешно сброшен!")
        print(f"   Username: {admin_user.username}")
        print(f"   Password: {new_password}")
        print(f"   Role: {admin_user.role}")

if __name__ == "__main__":
    reset_admin_password()
