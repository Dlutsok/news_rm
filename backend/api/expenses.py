"""
API endpoints для мониторинга расходов
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from datetime import datetime, date
from sqlmodel import Session, select, func
from sqlalchemy import text
from database.models import (
    ExpenseCreate, ExpenseRead, ExpenseSummary, 
    Expense, User, ExpenseType, ProjectType
)
from database.connection import get_session
from api.dependencies import require_staff, require_analytics_access, get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Expenses"])


# Словари для человекочитаемых названий
PROJECT_NAMES = {
    ProjectType.GYNECOLOGY.value: "Gynecology School",
    ProjectType.PEDIATRICS.value: "Pediatrics School",
    ProjectType.THERAPY.value: "Therapy School"
}

EXPENSE_TYPE_NAMES = {
    ExpenseType.NEWS_CREATION: "Создание новости",
    ExpenseType.PHOTO_REGENERATION: "Перегенерация фото",
    ExpenseType.GPT_MESSAGE: "GPT сообщение",
    ExpenseType.TELEGRAM_POST: "Создание Telegram поста"
}

EXPENSE_TYPE_COSTS = {
    ExpenseType.NEWS_CREATION: 40.0,
    ExpenseType.PHOTO_REGENERATION: 10.0,
    ExpenseType.GPT_MESSAGE: 5.0,
    ExpenseType.TELEGRAM_POST: 20.0
}


@router.get("/", response_model=dict)
async def get_expenses(
    date_from: Optional[date] = Query(None, description="Дата начала периода"),
    date_to: Optional[date] = Query(None, description="Дата окончания периода"),
    user_id: Optional[int] = Query(None, description="ID пользователя"),
    project: Optional[str] = Query(None, description="Проект"),
    expense_type: Optional[ExpenseType] = Query(None, description="Тип расхода"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_analytics_access)
):
    """
    Получить список расходов с фильтрацией
    """
    try:
        # Базовый запрос
        query = select(Expense, User.username).join(User, Expense.user_id == User.id)
        
        # Применяем фильтры
        if date_from:
            query = query.where(func.date(Expense.created_at) >= date_from)
        if date_to:
            query = query.where(func.date(Expense.created_at) <= date_to)
        if user_id:
            query = query.where(Expense.user_id == user_id)
        if project:
            query = query.where(Expense.project == project)
        if expense_type:
            query = query.where(Expense.expense_type == expense_type)
            
        # Сортировка по дате создания (новые сначала)
        query = query.order_by(Expense.created_at.desc())
        
        # Выполняем запрос
        results = session.exec(query).all()
        
        # Формируем ответ
        expenses = []
        for expense, username in results:
            expense_data = {
                "id": expense.id,
                "date": expense.created_at.date().isoformat(),
                "user": username,
                "userId": expense.user_id,
                "project": expense.project,
                "projectName": PROJECT_NAMES.get(expense.project, expense.project),
                "expenseType": expense.expense_type,
                "expenseTypeName": EXPENSE_TYPE_NAMES.get(expense.expense_type, expense.expense_type),
                "amount": float(expense.amount),
                "description": expense.description or f"{EXPENSE_TYPE_NAMES.get(expense.expense_type)} для проекта {PROJECT_NAMES.get(expense.project)}"
            }
            expenses.append(expense_data)
        
        return {"expenses": expenses}
        
    except Exception as e:
        logger.error(f"Error fetching expenses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении данных о расходах"
        )


@router.post("/", response_model=ExpenseRead)
async def create_expense(
    expense_data: ExpenseCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_analytics_access)
):
    """
    Создать новый расход
    """
    try:
        # Проверяем существование пользователя
        user = session.get(User, expense_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Определяем проект: используем проект из запроса или проект пользователя
        project = expense_data.project or user.project
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Проект не указан и не привязан к пользователю"
            )
        
        # Создаем расход
        expense = Expense(
            user_id=expense_data.user_id,
            project=project.value if hasattr(project, 'value') else str(project),
            expense_type=expense_data.expense_type.value if hasattr(expense_data.expense_type, 'value') else str(expense_data.expense_type),
            amount=expense_data.amount,
            description=expense_data.description,
            related_article_id=expense_data.related_article_id,
            related_session_id=expense_data.related_session_id
        )
        
        session.add(expense)
        session.commit()
        session.refresh(expense)
        
        logger.info(f"Created expense: {expense.id} for user {user.username}, amount: {expense.amount}")
        
        return ExpenseRead(
            id=expense.id,
            user_id=expense.user_id,
            project=expense.project,
            expense_type=expense.expense_type,
            amount=expense.amount,
            description=expense.description,
            related_article_id=expense.related_article_id,
            related_session_id=expense.related_session_id,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
            user_name=user.username,
            project_name=PROJECT_NAMES.get(expense.project),
            expense_type_name=EXPENSE_TYPE_NAMES.get(expense.expense_type)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating expense: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании расхода"
        )


@router.get("/summary", response_model=ExpenseSummary)
async def get_expenses_summary(
    date_from: Optional[date] = Query(None, description="Дата начала периода"),
    date_to: Optional[date] = Query(None, description="Дата окончания периода"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_analytics_access)
):
    """
    Получить сводку расходов
    """
    try:
        # Базовый запрос
        query = select(Expense).join(User, Expense.user_id == User.id)
        
        # Применяем фильтры по датам
        if date_from:
            query = query.where(func.date(Expense.created_at) >= date_from)
        if date_to:
            query = query.where(func.date(Expense.created_at) <= date_to)
            
        expenses = session.exec(query).all()
        
        # Общая сумма и количество
        total_amount = sum(expense.amount for expense in expenses)
        expenses_count = len(expenses)
        
        # Группировка по проектам
        by_project = {}
        for project_type in ProjectType:
            project_expenses = [e for e in expenses if e.project == project_type]
            by_project[project_type.value] = {
                "name": PROJECT_NAMES.get(project_type.value, project_type.value),
                "amount": sum(e.amount for e in project_expenses),
                "count": len(project_expenses)
            }
        
        # Группировка по пользователям
        by_user = {}
        user_expenses = {}
        for expense in expenses:
            if expense.user_id not in user_expenses:
                user_expenses[expense.user_id] = []
            user_expenses[expense.user_id].append(expense)
            
        for user_id, user_expense_list in user_expenses.items():
            user = session.get(User, user_id)
            if user:
                by_user[user_id] = {
                    "name": user.username,
                    "amount": sum(e.amount for e in user_expense_list),
                    "count": len(user_expense_list)
                }
        
        # Группировка по типам расходов
        by_type = {}
        for expense_type in ExpenseType:
            type_expenses = [e for e in expenses if e.expense_type == expense_type]
            by_type[expense_type] = {
                "name": EXPENSE_TYPE_NAMES.get(expense_type, expense_type),
                "amount": sum(e.amount for e in type_expenses),
                "count": len(type_expenses),
                "cost_per_unit": EXPENSE_TYPE_COSTS.get(expense_type, 0)
            }
        
        return ExpenseSummary(
            total_amount=total_amount,
            expenses_count=expenses_count,
            by_project=by_project,
            by_user=by_user,
            by_type=by_type
        )
        
    except Exception as e:
        logger.error(f"Error getting expenses summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении сводки расходов"
        )


@router.post("/bulk", response_model=dict)
async def create_bulk_expenses(
    expenses_data: List[ExpenseCreate],
    session: Session = Depends(get_session),
    current_user: User = Depends(require_analytics_access)
):
    """
    Создать несколько расходов одновременно
    """
    try:
        created_expenses = []
        
        for expense_data in expenses_data:
            # Проверяем существование пользователя
            user = session.get(User, expense_data.user_id)
            if not user:
                continue  # Пропускаем несуществующих пользователей
            
            expense = Expense(
                user_id=expense_data.user_id,
                project=expense_data.project.value if hasattr(expense_data.project, 'value') else str(expense_data.project),
                expense_type=expense_data.expense_type.value if hasattr(expense_data.expense_type, 'value') else str(expense_data.expense_type),
                amount=expense_data.amount,
                description=expense_data.description,
                related_article_id=expense_data.related_article_id,
                related_session_id=expense_data.related_session_id
            )
            
            session.add(expense)
            created_expenses.append(expense)
        
        session.commit()
        
        logger.info(f"Created {len(created_expenses)} expenses in bulk by {current_user.username}")
        
        return {
            "created_count": len(created_expenses),
            "message": f"Создано {len(created_expenses)} расходов"
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating bulk expenses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при массовом создании расходов"
        )


# Вспомогательная функция для автоматического создания расходов
async def auto_create_expense(
    user_id: int,
    project: ProjectType,
    expense_type: ExpenseType,
    description: Optional[str] = None,
    related_article_id: Optional[int] = None,
    related_session_id: Optional[str] = None,
    session: Session = None
):
    """
    Автоматически создать расход (для использования в других сервисов)
    """
    logger.info(f"[ENTRY] auto_create_expense called: user_id={user_id}, project={project}, expense_type={expense_type}, session={session is not None}")
    if not session:
        from database.connection import engine
        with Session(engine) as session:
            return await auto_create_expense(
                user_id, project, expense_type, description,
                related_article_id, related_session_id, session
            )
    
    try:
        # Получаем пользователя для определения проекта
        user = session.get(User, user_id)
        if not user:
            raise ValueError(f"Пользователь с ID {user_id} не найден")
        
        # Используем проект пользователя, если не указан
        final_project = project
        if not final_project and user.project:
            try:
                # Сначала попробуем как enum value
                final_project = ProjectType(user.project)
            except ValueError:
                try:
                    # Попробуем как enum name (GYNECOLOGY -> ProjectType.GYNECOLOGY)
                    final_project = ProjectType[user.project]
                except KeyError:
                    logger.warning(f"Unknown user project type: {user.project}")
                    final_project = ProjectType.GYNECOLOGY  # fallback
        
        if not final_project:
            raise ValueError("Проект не указан и не привязан к пользователю")
        
        amount = EXPENSE_TYPE_COSTS.get(expense_type, 0.0)

        # Нормализуем проект к строковому значению enum (value)
        def normalize_project_to_value(p) -> str:
            if isinstance(p, ProjectType):
                return p.value
            if isinstance(p, str) and p:
                try:
                    # пробуем как value (например, 'rusmedical' / 'gynecology.school')
                    return ProjectType(p).value
                except Exception:
                    try:
                        # пробуем как имя (например, 'RUSMEDICAL' / 'GYNECOLOGY')
                        return ProjectType[p].value
                    except Exception:
                        # Если ничего не сработало, возвращаем как есть
                        logger.warning(f"Unknown project type: {p}")
                        return p
            return ""

        final_project_value = normalize_project_to_value(final_project)
        # Приводим проект к enum ProjectType строго по value
        try:
            final_project_enum = ProjectType(final_project_value)
        except Exception:
            logger.warning(f"Cannot coerce project to enum, using raw value: '{final_project_value}'")
            final_project_enum = None

        # Приводим тип расхода к enum ExpenseType
        try:
            final_expense_type = expense_type if isinstance(expense_type, ExpenseType) else ExpenseType(str(expense_type))
        except Exception:
            logger.warning(f"Cannot coerce expense_type to enum, using default GPT_MESSAGE. Incoming: {expense_type}")
            final_expense_type = ExpenseType.GPT_MESSAGE

        logger.info(
            f"[DEBUG] final_project={final_project} type={type(final_project)} -> value='{final_project_value}', as_enum={final_project_enum}; "
            f"expense_type_in={expense_type} -> as_enum={final_expense_type}"
        )
        logger.info(
            f"[Expenses] auto_create_expense: user_id={user_id}, incoming_project={final_project}, normalized='{final_project_value}', "
            f"expense_type={final_expense_type}, amount={amount}"
        )

        # Создаем объект Expense через SQLModel, передавая строковые значения
        expense = Expense(
            user_id=user_id,
            project=(final_project_enum.value if final_project_enum is not None else final_project_value),
            expense_type=final_expense_type.value,
            amount=amount,
            description=description or f"{EXPENSE_TYPE_NAMES.get(final_expense_type)} для проекта {PROJECT_NAMES.get((final_project_enum.value if final_project_enum else final_project_value))}",
            related_article_id=related_article_id,
            related_session_id=related_session_id,
        )
        
        session.add(expense)
        session.commit()
        session.refresh(expense)
        logger.info(f"Auto-created expense: id={expense.id}, user={user_id}, project='{final_project_value}', type={expense.expense_type}, amount={amount}")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error auto-creating expense: {e}")
        return None