"""
Сервис для управления настройками приложения
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from database.connection import DatabaseSession
from database.models import BitrixProjectSettings, AppSettings
from models.schemas import (
    BitrixProjectSettingsCreate, 
    BitrixProjectSettingsUpdate,
    BitrixProjectSettingsRead,
    AppSettingsCreate,
    AppSettingsUpdate,
    AppSettingsRead
)
import logging

logger = logging.getLogger(__name__)


class SettingsService:
    """Сервис для управления настройками приложения"""
    
    def __init__(self):
        self.session = DatabaseSession
    
    # Методы для Bitrix проектов
    
    def get_bitrix_projects(self) -> List[BitrixProjectSettingsRead]:
        """Получить все настройки проектов Bitrix"""
        with self.session() as session:
            stmt = select(BitrixProjectSettings).order_by(BitrixProjectSettings.project_code)
            projects = session.exec(stmt).all()
            return [BitrixProjectSettingsRead(**project.__dict__) for project in projects]
    
    def get_bitrix_project(self, project_code: str) -> Optional[BitrixProjectSettingsRead]:
        """Получить настройки конкретного проекта"""
        with self.session() as session:
            stmt = select(BitrixProjectSettings).where(BitrixProjectSettings.project_code == project_code)
            project = session.exec(stmt).first()
            if project:
                return BitrixProjectSettingsRead(**project.__dict__)
            return None
    
    def create_bitrix_project(self, project_data: BitrixProjectSettingsCreate) -> BitrixProjectSettingsRead:
        """Создать настройки проекта"""
        with self.session() as session:
            project = BitrixProjectSettings(**project_data.dict())
            session.add(project)
            session.commit()
            session.refresh(project)
            return BitrixProjectSettingsRead.model_validate(project)
    
    def update_bitrix_project(self, project_code: str, project_data: BitrixProjectSettingsUpdate) -> Optional[BitrixProjectSettingsRead]:
        """Обновить настройки проекта"""
        import logging
        logger = logging.getLogger(__name__)

        with self.session() as session:
            stmt = select(BitrixProjectSettings).where(BitrixProjectSettings.project_code == project_code)
            project = session.exec(stmt).first()

            if not project:
                logger.warning(f"[DEBUG] Project {project_code} not found in database")
                return None

            logger.info(f"[DEBUG] Found project: {project.project_code}, current token: {'*' * (len(project.api_token or '') - 4) + (project.api_token or '')[-4:]}")

            # Обновляем только переданные поля
            update_data = project_data.dict(exclude_unset=True)
            logger.info(f"[DEBUG] Updating fields: {list(update_data.keys())}")

            for field, value in update_data.items():
                old_value = getattr(project, field, None)
                setattr(project, field, value)
                if field == "api_token":
                    logger.info(f"[DEBUG] Token updated from {'*' * (len(str(old_value or '')) - 4) + str(old_value or '')[-4:]} to {'*' * (len(str(value or '')) - 4) + str(value or '')[-4:]}")

            project.updated_at = datetime.utcnow()
            session.add(project)
            session.commit()
            session.refresh(project)

            logger.info(f"[DEBUG] Project saved with token: {'*' * (len(project.api_token or '') - 4) + (project.api_token or '')[-4:]}")
            return BitrixProjectSettingsRead.model_validate(project)
    
    def delete_bitrix_project(self, project_code: str) -> bool:
        """Удалить настройки проекта"""
        with self.session() as session:
            stmt = select(BitrixProjectSettings).where(BitrixProjectSettings.project_code == project_code)
            project = session.exec(stmt).first()
            
            if not project:
                return False
            
            session.delete(project)
            session.commit()
            return True
    
    # Методы для общих настроек
    
    def get_app_settings(self, category: Optional[str] = None) -> List[AppSettingsRead]:
        """Получить настройки приложения"""
        with self.session() as session:
            stmt = select(AppSettings)
            if category:
                stmt = stmt.where(AppSettings.category == category)
            stmt = stmt.order_by(AppSettings.category, AppSettings.setting_key)
            
            settings = session.exec(stmt).all()
            return [AppSettingsRead(**setting.__dict__) for setting in settings]
    
    def get_app_setting(self, setting_key: str) -> Optional[AppSettingsRead]:
        """Получить конкретную настройку"""
        with self.session() as session:
            stmt = select(AppSettings).where(AppSettings.setting_key == setting_key)
            setting = session.exec(stmt).first()
            if setting:
                return AppSettingsRead(**setting.__dict__)
            return None
    
    def create_app_setting(self, setting_data: AppSettingsCreate) -> AppSettingsRead:
        """Создать настройку"""
        with self.session() as session:
            setting = AppSettings(**setting_data.dict())
            session.add(setting)
            session.commit()
            session.refresh(setting)
            return AppSettingsRead.model_validate(setting)
    
    def update_app_setting(self, setting_key: str, setting_data: AppSettingsUpdate) -> Optional[AppSettingsRead]:
        """Обновить настройку"""
        with self.session() as session:
            stmt = select(AppSettings).where(AppSettings.setting_key == setting_key)
            setting = session.exec(stmt).first()
            
            if not setting:
                return None
            
            # Обновляем только переданные поля
            update_data = setting_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(setting, field, value)
            
            setting.updated_at = datetime.utcnow()
            session.add(setting)
            session.commit()
            session.refresh(setting)
            return AppSettingsRead.model_validate(setting)
    
    def delete_app_setting(self, setting_key: str) -> bool:
        """Удалить настройку"""
        with self.session() as session:
            stmt = select(AppSettings).where(AppSettings.setting_key == setting_key)
            setting = session.exec(stmt).first()
            
            if not setting:
                return False
            
            session.delete(setting)
            session.commit()
            return True
    
    def initialize_default_settings(self):
        """Инициализация настроек по умолчанию"""
        try:
            # Проверяем, есть ли уже проекты
            existing_projects = self.get_bitrix_projects()
            if not existing_projects:
                # Создаем проекты по умолчанию (берем значения из config, если заданы)
                from core.config import settings as app_settings
                bp = app_settings.BITRIX_PROJECTS or {}
                def cfg(code, key, default=""):
                    return (bp.get(code, {}) or {}).get(key, default)
                def cfg_int(code, key, default=38):
                    try:
                        return int((bp.get(code, {}) or {}).get(key, default) or default)
                    except Exception:
                        return default

                default_projects = [
                    BitrixProjectSettingsCreate(
                        project_code="GS",
                        project_name=cfg("GS", "name", "gynecology.school"),
                        display_name=cfg("GS", "display_name", "Гинекология и акушерство"),
                        api_url=cfg("GS", "api_url", "http://94.241.140.236/api/ai_news_import.php"),
                        api_token=cfg("GS", "api_token", ""),
                        iblock_id=cfg_int("GS", "iblock_id", 38),
                        description="Проект по гинекологии и акушерству"
                    ),
                    BitrixProjectSettingsCreate(
                        project_code="TS",
                        project_name=cfg("TS", "name", "therapy.school"),
                        display_name=cfg("TS", "display_name", "Терапия и общая медицина"),
                        api_url=cfg("TS", "api_url", ""),
                        api_token=cfg("TS", "api_token", ""),
                        iblock_id=cfg_int("TS", "iblock_id", 38),
                        description="Проект по терапии и общей медицине"
                    ),
                    BitrixProjectSettingsCreate(
                        project_code="PS",
                        project_name=cfg("PS", "name", "pediatrics.school"),
                        display_name=cfg("PS", "display_name", "Педиатрия и детская медицина"),
                        api_url=cfg("PS", "api_url", ""),
                        api_token=cfg("PS", "api_token", ""),
                        iblock_id=cfg_int("PS", "iblock_id", 38),
                        description="Проект по педиатрии и детской медицине"
                    )
                ]
                
                for project_data in default_projects:
                    try:
                        existing = self.get_bitrix_project(project_data.project_code)
                        if not existing:
                            self.create_bitrix_project(project_data)
                            logger.info(f"Created project {project_data.project_code}")
                        else:
                            logger.info(f"Project {project_data.project_code} already exists")
                    except Exception as e:
                        logger.error(f"Error creating project {project_data.project_code}: {e}")
                
                logger.info("Initialized default Bitrix projects")
            
            # Создаем базовые настройки приложения
            default_app_settings = [
                AppSettingsCreate(
                    setting_key="openai_api_key",
                    setting_value="",
                    setting_type="string",
                    description="API ключ для OpenAI",
                    category="openai"
                ),
                AppSettingsCreate(
                    setting_key="openai_model",
                    setting_value="gpt-4",
                    setting_type="string", 
                    description="Модель OpenAI для генерации",
                    category="openai"
                ),
                AppSettingsCreate(
                    setting_key="news_parsing_limit",
                    setting_value="100",
                    setting_type="int",
                    description="Лимит новостей для парсинга за раз",
                    category="parsing"
                ),
                AppSettingsCreate(
                    setting_key="auto_publish_enabled",
                    setting_value="false",
                    setting_type="bool",
                    description="Автоматическая публикация статей",
                    category="publishing"
                )
            ]
            
            for setting_data in default_app_settings:
                existing = self.get_app_setting(setting_data.setting_key)
                if not existing:
                    self.create_app_setting(setting_data)
            
            logger.info("Initialized default app settings")
            
        except Exception as e:
            logger.error(f"Error initializing default settings: {e}")
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Получить все настройки для фронтенда"""
        return {
            "bitrix_projects": self.get_bitrix_projects(),
            "app_settings": self.get_app_settings()
        }


# Создаем экземпляр сервиса
settings_service = SettingsService()