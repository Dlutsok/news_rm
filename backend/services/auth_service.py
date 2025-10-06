"""
Сервис аутентификации и авторизации
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select
from database.connection import engine
from database.models import User, UserRole, ProjectType, Expense
from core.config import settings

# Контекст для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Сервис для работы с аутентификацией и авторизацией"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверить пароль"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Хэшировать пароль"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создать JWT токен"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        """Проверить JWT токен и получить username"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except JWTError:
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Получить пользователя по username"""
        with Session(engine) as session:
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()
            return user
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """Аутентифицировать пользователя"""
        user = AuthService.get_user_by_username(username)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def create_user(username: str, password: str, role: UserRole = UserRole.STAFF, project: Optional[str] = None) -> User:
        """Создать нового пользователя"""
        hashed_password = AuthService.get_password_hash(password)
        
        with Session(engine) as session:
            # Проверяем, что пользователь с таким username не существует
            existing_user = session.exec(
                select(User).where(User.username == username)
            ).first()
            
            if existing_user:
                raise ValueError(f"Пользователь с username '{username}' уже существует")
            
            # Нормализуем проект под допустимые значения enum (или оставляем пустым)
            normalized_project: Optional[str] = None
            try:
                if project:
                    try:
                        # Пробуем как значение enum
                        normalized_project = ProjectType(project).value
                    except ValueError:
                        try:
                            # Пробуем как имя enum (GYNECOLOGY)
                            normalized_project = ProjectType[project].value
                        except KeyError:
                            normalized_project = None
            except Exception:
                normalized_project = None

            user = User(
                username=username,
                hashed_password=hashed_password,
                role=role,
                project=normalized_project
            )
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            return user
    
    @staticmethod
    def get_users() -> list[User]:
        """Получить всех пользователей"""
        with Session(engine) as session:
            statement = select(User)
            users = session.exec(statement).all()
            return list(users)
    
    @staticmethod
    def initialize_admin():
        """Инициализировать администратора при первом запуске"""
        admin_username = settings.ADMIN_USERNAME
        admin_password = settings.ADMIN_PASSWORD
        
        with Session(engine) as session:
            # Проверяем, есть ли уже админ
            admin_user = session.exec(
                select(User).where(User.role == UserRole.ADMIN)
            ).first()
            
            if not admin_user:
                print(f"🔧 Creating initial admin user: {admin_username}")
                try:
                    AuthService.create_user(admin_username, admin_password, UserRole.ADMIN)
                    print("✅ Admin user created successfully")
                except ValueError as e:
                    print(f"⚠️ Admin user creation skipped: {e}")

    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Удалить пользователя по ID"""
        with Session(engine) as session:
            user = session.get(User, user_id)
            if not user:
                return False
            
            # Сначала удаляем все связанные расходы пользователя
            expenses_statement = select(Expense).where(Expense.user_id == user_id)
            expenses = session.exec(expenses_statement).all()
            for expense in expenses:
                session.delete(expense)
            
            # Теперь можно безопасно удалить пользователя
            session.delete(user)
            session.commit()
            return True

    @staticmethod
    def update_user_password(user_id: int, new_password: str) -> bool:
        """Обновить пароль пользователя"""
        with Session(engine) as session:
            user = session.get(User, user_id)
            if not user:
                return False
            user.hashed_password = AuthService.get_password_hash(new_password)
            session.add(user)
            session.commit()
            return True


# Создаем экземпляр сервиса
auth_service = AuthService()