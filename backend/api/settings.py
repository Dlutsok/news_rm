"""
API endpoints для управления настройками приложения
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from models.schemas import (
    BitrixProjectSettingsCreate,
    BitrixProjectSettingsUpdate, 
    BitrixProjectSettingsRead,
    AppSettingsCreate,
    AppSettingsUpdate,
    AppSettingsRead,
    SettingsResponse
)
from services.settings_service import settings_service
from services.extended_settings_service import extended_settings_service
from api.dependencies import require_admin, require_staff
from database.models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])


# Endpoints для Bitrix проектов

@router.get("/bitrix-projects", response_model=List[BitrixProjectSettingsRead])
async def get_bitrix_projects(current_user: User = Depends(require_staff)):
    """Получить все настройки проектов Bitrix"""
    try:
        logger.info(f"[DEBUG] GET request for ALL Bitrix projects")
        projects = settings_service.get_bitrix_projects()

        # Логируем токены для всех проектов
        for project in projects:
            if project.api_token:
                logger.info(f"[DEBUG] Project {project.project_code} has token: {'*' * (len(project.api_token) - 8) + project.api_token[-8:]}")
            else:
                logger.info(f"[DEBUG] Project {project.project_code} has NO token")

        return projects
    except Exception as e:
        logger.error(f"Error getting Bitrix projects: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения настроек проектов")


@router.get("/bitrix-projects/{project_code}", response_model=BitrixProjectSettingsRead)
async def get_bitrix_project(project_code: str, current_user: User = Depends(require_staff)):
    """Получить настройки конкретного проекта"""
    try:
        logger.info(f"[DEBUG] GET request for Bitrix project: {project_code}")
        project = settings_service.get_bitrix_project(project_code)
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")

        # Логируем что возвращаем (без полного токена)
        if project.api_token:
            logger.info(f"[DEBUG] Returning project with token: {'*' * (len(project.api_token) - 8) + project.api_token[-8:]}")
        else:
            logger.info(f"[DEBUG] Returning project with NO token")

        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Bitrix project {project_code}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения настроек проекта")


@router.post("/bitrix-projects", response_model=BitrixProjectSettingsRead)
async def create_bitrix_project(project_data: BitrixProjectSettingsCreate, current_user: User = Depends(require_admin)):
    """Создать настройки нового проекта"""
    try:
        # Проверяем, что проект с таким кодом не существует
        existing = settings_service.get_bitrix_project(project_data.project_code)
        if existing:
            raise HTTPException(status_code=400, detail="Проект с таким кодом уже существует")
        
        return settings_service.create_bitrix_project(project_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Bitrix project: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания проекта")


@router.put("/bitrix-projects/{project_code}", response_model=BitrixProjectSettingsRead)
async def update_bitrix_project(project_code: str, project_data: BitrixProjectSettingsUpdate, current_user: User = Depends(require_admin)):
    """Обновить настройки проекта"""
    try:
        # Логируем входящие данные
        logger.info(f"[DEBUG] Updating Bitrix project {project_code}")
        logger.info(f"[DEBUG] Received data: {project_data.dict(exclude_unset=True)}")

        # Специально проверяем api_token
        if project_data.api_token:
            logger.info(f"[DEBUG] API token being updated: {'*' * (len(project_data.api_token) - 4) + project_data.api_token[-4:]}")

        project = settings_service.update_bitrix_project(project_code, project_data)
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")

        logger.info(f"[DEBUG] Successfully updated project: {project.project_code}")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Bitrix project {project_code}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления настроек проекта")


@router.delete("/bitrix-projects/{project_code}")
async def delete_bitrix_project(project_code: str, current_user: User = Depends(require_admin)):
    """Удалить настройки проекта"""
    try:
        success = settings_service.delete_bitrix_project(project_code)
        if not success:
            raise HTTPException(status_code=404, detail="Проект не найден")
        return {"message": "Проект удален успешно"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Bitrix project {project_code}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления проекта")


# Endpoints для общих настроек

@router.get("/app-settings", response_model=List[AppSettingsRead])
async def get_app_settings(category: str = None, current_user: User = Depends(require_staff)):
    """Получить настройки приложения"""
    try:
        return settings_service.get_app_settings(category)
    except Exception as e:
        logger.error(f"Error getting app settings: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения настроек приложения")


@router.get("/app-settings/{setting_key}", response_model=AppSettingsRead)
async def get_app_setting(setting_key: str, current_user: User = Depends(require_staff)):
    """Получить конкретную настройку"""
    try:
        setting = settings_service.get_app_setting(setting_key)
        if not setting:
            raise HTTPException(status_code=404, detail="Настройка не найдена")
        return setting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting app setting {setting_key}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения настройки")


@router.post("/app-settings", response_model=AppSettingsRead)
async def create_app_setting(setting_data: AppSettingsCreate, current_user: User = Depends(require_admin)):
    """Создать новую настройку"""
    try:
        # Проверяем, что настройка с таким ключом не существует
        existing = settings_service.get_app_setting(setting_data.setting_key)
        if existing:
            raise HTTPException(status_code=400, detail="Настройка с таким ключом уже существует")
        
        return settings_service.create_app_setting(setting_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating app setting: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания настройки")


@router.put("/app-settings/{setting_key}", response_model=AppSettingsRead)
async def update_app_setting(setting_key: str, setting_data: AppSettingsUpdate, current_user: User = Depends(require_admin)):
    """Обновить настройку"""
    try:
        setting = settings_service.update_app_setting(setting_key, setting_data)
        if not setting:
            raise HTTPException(status_code=404, detail="Настройка не найдена")
        return setting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating app setting {setting_key}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления настройки")


@router.delete("/app-settings/{setting_key}")
async def delete_app_setting(setting_key: str, current_user: User = Depends(require_admin)):
    """Удалить настройку"""
    try:
        success = settings_service.delete_app_setting(setting_key)
        if not success:
            raise HTTPException(status_code=404, detail="Настройка не найдена")
        return {"message": "Настройка удалена успешно"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting app setting {setting_key}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления настройки")


# Endpoints для системных настроек

@router.get("/system", response_model=Dict[str, Any])
async def get_system_settings(current_user: User = Depends(require_admin)):
    """Получить системные настройки"""
    try:
        logger.info("Getting system settings...")
        system_settings = settings_service.get_app_settings(category="system")
        logger.info(f"Found {len(system_settings)} existing system settings")
        
        # Преобразуем в удобный формат для фронтенда
        settings_dict = {}
        for setting in system_settings:
            settings_dict[setting.setting_key] = {
                "value": setting.setting_value,
                "type": setting.setting_type,
                "description": setting.description
            }
        
        # Если настроек мало, создаем/обновляем все базовые
        default_settings = extended_settings_service.get_default_system_settings()
        logger.info(f"Default settings count: {len(default_settings)}")
        
        for key, config in default_settings.items():
            if key not in settings_dict:
                logger.info(f"Creating missing setting: {key}")
                # Проверяем, есть ли настройка в БД (может быть в другой категории)
                existing_setting = settings_service.get_app_setting(key)
                if existing_setting:
                    logger.info(f"Setting {key} exists in category {existing_setting.category}, adding to response")
                    settings_dict[key] = {
                        "value": existing_setting.setting_value,
                        "type": existing_setting.setting_type,
                        "description": existing_setting.description
                    }
                else:
                    # Создаем отсутствующую настройку
                    try:
                        created_setting = settings_service.create_app_setting(AppSettingsCreate(
                            setting_key=key,
                            setting_value=config["default_value"],
                            setting_type=config["type"],
                            description=config["description"],
                            category="system"
                        ))
                        settings_dict[key] = {
                            "value": created_setting.setting_value,
                            "type": created_setting.setting_type,
                            "description": created_setting.description
                        }
                        logger.info(f"Created setting: {key}")
                    except Exception as e:
                        logger.warning(f"Failed to create setting {key}: {e}")
                        # Используем значения по умолчанию, если не удалось создать
                        settings_dict[key] = {
                            "value": config["default_value"],
                            "type": config["type"],
                            "description": config["description"]
                        }
        
        logger.info(f"Returning {len(settings_dict)} settings")
        # Добавляем в системные настройки выбор модели генерации OpenAI
        try:
            existing_generation_model = settings_service.get_app_setting("openai_generation_model")
            if not existing_generation_model:
                logger.info("Creating openai_generation_model setting in 'openai' category with default 'gpt-4o'")
                created = settings_service.create_app_setting(AppSettingsCreate(
                    setting_key="openai_generation_model",
                    setting_value="gpt-4o",
                    setting_type="string",
                    description="Модель OpenAI для генерации статей",
                    category="openai"
                ))
                generation_model_setting = created
            else:
                generation_model_setting = existing_generation_model
            # Делаем её видимой в системной панели настроек
            settings_dict["openai_generation_model"] = {
                "value": generation_model_setting.setting_value,
                "type": "string",
                "description": "Модель OpenAI для генерации статей (gpt-4o-mini, gpt-4o, gpt-4, gpt-3.5-turbo-16k)"
            }

            # Также добавляем настройки модели для выжимки
            def ensure_setting(key: str, default_value: str, desc: str, stype: str = "string"):
                s = settings_service.get_app_setting(key)
                if not s:
                    created = settings_service.create_app_setting(AppSettingsCreate(
                        setting_key=key,
                        setting_value=default_value,
                        setting_type=stype,
                        description=desc,
                        category="openai"
                    ))
                    return created
                return s

            summary_model = ensure_setting(
                "openai_summary_model",
                "gpt-4o-mini",
                "Модель OpenAI для выжимки (gpt-4o-mini, gpt-4o, gpt-4, gpt-3.5-turbo-16k)"
            )
            summary_temperature = ensure_setting(
                "openai_summary_temperature",
                "0.3",
                "Температура для выжимки",
                "float"
            )
            summary_max_tokens = ensure_setting(
                "openai_summary_max_tokens",
                "1000",
                "Max tokens для выжимки",
                "int"
            )

            settings_dict["openai_summary_model"] = {
                "value": summary_model.setting_value,
                "type": "string",
                "description": "Модель OpenAI для выжимки (gpt-4o-mini, gpt-4o, gpt-4, gpt-3.5-turbo-16k)"
            }
            settings_dict["openai_summary_temperature"] = {
                "value": summary_temperature.setting_value,
                "type": "float",
                "description": "Температура для выжимки"
            }
            settings_dict["openai_summary_max_tokens"] = {
                "value": summary_max_tokens.setting_value,
                "type": "int",
                "description": "Max tokens для выжимки"
            }

            # Расходы (в рублях)
            try:
                expenses_setting = settings_service.get_app_setting("expenses_total_rub")
                if not expenses_setting:
                    created_expenses = settings_service.create_app_setting(AppSettingsCreate(
                        setting_key="expenses_total_rub",
                        setting_value="0",
                        setting_type="int",
                        description="Суммарные расходы в рублях",
                        category="finance"
                    ))
                    expenses_setting = created_expenses
                settings_dict["expenses_total_rub"] = {
                    "value": expenses_setting.setting_value,
                    "type": "int",
                    "description": "Суммарные расходы в рублях"
                }
            except Exception as e:
                logger.warning(f"Failed to ensure expenses_total_rub setting: {e}")
        except Exception as add_e:
            logger.warning(f"Failed to ensure openai_generation_model in system settings: {add_e}")

        return {"settings": settings_dict}
    except Exception as e:
        logger.error(f"Error getting system settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка получения системных настроек")


@router.put("/system", response_model=Dict[str, str])
async def update_system_settings(
    settings_data: Dict[str, str], 
    current_user: User = Depends(require_admin)
):
    """Обновить системные настройки"""
    try:
        updated_count = 0
        for key, value in settings_data.items():
            setting = settings_service.update_app_setting(
                key, 
                AppSettingsUpdate(setting_value=value)
            )
            if setting:
                updated_count += 1
        
        return {
            "message": f"Обновлено настроек: {updated_count}",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error updating system settings: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления системных настроек")


# Комбинированные endpoints

@router.get("/all", response_model=Dict[str, Any])
async def get_all_settings(current_user: User = Depends(require_staff)):
    """Получить все настройки приложения"""
    try:
        return settings_service.get_all_settings()
    except Exception as e:
        logger.error(f"Error getting all settings: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения настроек")


@router.post("/initialize")
async def initialize_default_settings(current_user: User = Depends(require_admin)):
    """Инициализировать настройки по умолчанию"""
    try:
        settings_service.initialize_default_settings()
        return {"message": "Настройки по умолчанию инициализированы"}
    except Exception as e:
        logger.error(f"Error initializing default settings: {e}")
        raise HTTPException(status_code=500, detail="Ошибка инициализации настроек")


@router.get("/all-categorized")
async def get_all_settings_categorized(current_user: User = Depends(require_staff)):
    """Получить все настройки, сгруппированные по категориям"""
    try:
        return extended_settings_service.get_settings_by_categories()
    except Exception as e:
        logger.error(f"Error getting categorized settings: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения настроек")


@router.post("/initialize-extended")
async def initialize_extended_settings(current_user: User = Depends(require_admin)):
    """Инициализировать расширенный набор настроек"""
    try:
        extended_settings_service.initialize_all_settings()
        return {"message": "Расширенные настройки инициализированы"}
    except Exception as e:
        logger.error(f"Error initializing extended settings: {e}")
        raise HTTPException(status_code=500, detail="Ошибка инициализации расширенных настроек")


@router.post("/test-bitrix/{project_code}")
async def test_bitrix_connection(project_code: str, current_user: User = Depends(require_admin)):
    """Тестировать подключение к Bitrix для проекта"""
    try:
        # Получаем настройки проекта
        project = settings_service.get_bitrix_project(project_code)
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")
        
        # Здесь можно добавить логику тестирования подключения
        # Пока просто проверяем наличие URL и токена
        if not project.api_url or not project.api_token:
            return {
                "success": False,
                "message": "URL или токен не настроены"
            }
        
        # TODO: Добавить реальное тестирование подключения к Bitrix API
        return {
            "success": True,
            "message": f"Настройки для проекта {project.display_name} выглядят корректно"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing Bitrix connection for {project_code}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка тестирования подключения")