"""
API endpoints для управления пользователями
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from database.models import UserCreate, UserRead, User
from services.auth_service import auth_service
from api.dependencies import require_admin, require_staff
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Users"])


@router.post("/create", response_model=UserRead)
async def create_user(
    user_data: UserCreate, 
    current_user: User = Depends(require_admin)
):
    """
    Создать нового пользователя (только для администраторов)
    """
    try:
        # Создаем пользователя
        new_user = auth_service.create_user(
            username=user_data.username,
            password=user_data.password,
            role=user_data.role,
            project=user_data.project
        )
        
        logger.info(f"Admin {current_user.username} created new user: {new_user.username} with role {new_user.role}")
        
        return UserRead(
            id=new_user.id,
            username=new_user.username,
            role=new_user.role,
            project=new_user.project,
            created_at=new_user.created_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user creation"
        )


@router.get("/", response_model=List[UserRead])
async def get_users(current_user: User = Depends(require_admin)):
    """
    Получить список всех пользователей (только для администраторов)
    """
    try:
        users = auth_service.get_users()
        
        return [
            UserRead(
                id=user.id,
                username=user.username,
                role=user.role,
                project=user.project,
                created_at=user.created_at
            )
            for user in users
        ]
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching users"
        )


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(current_user: User = Depends(require_staff)):
    """
    Получить профиль текущего пользователя
    """
    return UserRead(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        project=current_user.project,
        created_at=current_user.created_at
    )


@router.delete("/{user_id}")
async def delete_user(user_id: int, current_user: User = Depends(require_admin)):
    """
    Удалить пользователя (только админ)
    """
    try:
        if auth_service.delete_user(user_id):
            return {"message": "Пользователь удален"}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while deleting user")


@router.post("/{user_id}/password")
async def update_user_password(user_id: int, payload: dict, current_user: User = Depends(require_admin)):
    """
    Сменить пароль пользователя (только админ)
    """
    try:
        new_password = payload.get("password")
        if not new_password or len(new_password) < 6:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный пароль")
        if auth_service.update_user_password(user_id, new_password):
            return {"message": "Пароль обновлен"}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating password for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while updating password")