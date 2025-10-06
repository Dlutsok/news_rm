"""
API endpoints для авторизации и аутентификации
"""

from fastapi import APIRouter, HTTPException, Depends, status
from datetime import timedelta
from database.models import UserLogin, Token, UserRead, User
from services.auth_service import auth_service
from api.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """
    Авторизация пользователя
    """
    try:
        # Аутентифицируем пользователя
        user = auth_service.authenticate_user(
            user_credentials.username, 
            user_credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Создаем токен
        access_token = auth_service.create_access_token(
            data={"sub": user.username}
        )
        
        logger.info(f"User {user.username} logged in successfully")
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Получить информацию о текущем пользователе
    """
    logger.info(f"Get current user info for: {current_user.username}, role: {current_user.role}")
    return UserRead(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        project=current_user.project,
        created_at=current_user.created_at
    )


@router.post("/verify-token")
async def verify_token(current_user: User = Depends(get_current_user)):
    """
    Проверить валидность токена
    """
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "project": current_user.project
        }
    }