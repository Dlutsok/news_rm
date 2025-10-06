"""
Зависимости для авторизации и проверки ролей
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from database.models import User, UserRole
from services.auth_service import auth_service


# Схемы безопасности
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Получить текущего пользователя из JWT токена
    """
    import logging
    logger = logging.getLogger(__name__)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Проверяем токен
    logger.info(f"Verifying token: {credentials.credentials[:20]}...")
    username = auth_service.verify_token(credentials.credentials)
    if username is None:
        logger.warning("Token verification failed")
        raise credentials_exception

    logger.info(f"Token verified for username: {username}")

    # Получаем пользователя
    user = auth_service.get_user_by_username(username)
    if user is None:
        logger.warning(f"User not found: {username}")
        raise credentials_exception

    logger.info(f"User authenticated: {user.username}, role: {user.role}")
    return user


async def require_staff(current_user: User = Depends(get_current_user)) -> User:
    """
    Зависимость: требует любого авторизованного пользователя (staff или admin)
    """
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Зависимость: требует администратора
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Administrator role required."
        )
    return current_user


async def require_analytics_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Зависимость: требует доступа к аналитике (администратор или аналитик)
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.ANALYST):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Analytics access required (admin or analyst role)."
        )
    return current_user


# Опциональная авторизация (может быть полезна в будущем)
async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Optional[User]:
    """
    Получить текущего пользователя (опционально)
    Возвращает None если токен отсутствует или невалидный
    """
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    if not token:
        # Пробуем взять токен из HttpOnly cookie для запросов через Next.js rewrites
        token = request.cookies.get("auth_token")
    if not token:
        return None
    try:
        username = auth_service.verify_token(token)
        if username is None:
            return None
        
        user = auth_service.get_user_by_username(username)
        return user
    except:
        return None