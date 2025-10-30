#!/usr/bin/env python3
"""
Тест генерации выжимки статьи (полная симуляция endpoint)
"""

import os
import sys
import time
import asyncio
from dotenv import load_dotenv

# Устанавливаем DATABASE_URL перед импортом
os.environ['DATABASE_URL'] = "postgresql://postgres:medical2024@localhost:5432/news_aggregator"

sys.path.insert(0, '.')

from database.connection import DatabaseSession
from database.models import Article, ProjectType
from services.ai_service import AIService
from sqlmodel import select

# Загружаем переменные окружения
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

print("=" * 60)
print("🧪 Тест генерации выжимки статьи")
print("=" * 60)


async def test_summarize_endpoint():
    """Полная симуляция работы endpoint /api/news-generation/summarize"""

    print("\n📝 Шаг 1: Получаем статью из БД")
    print("-" * 60)

    start_time = time.time()

    try:
        with DatabaseSession() as session:
            # Получаем последнюю статью
            stmt = select(Article).order_by(Article.id.desc()).limit(1)
            article = session.exec(stmt).first()

            if not article:
                print("❌ Статей в БД нет!")
                return False

            # Сохраняем данные статьи перед закрытием сессии
            article_id = article.id
            article_title = article.title
            article_content = article.content

            elapsed = time.time() - start_time
            print(f"✅ Статья получена за {elapsed:.2f}s")
            print(f"ID: {article_id}")
            print(f"Заголовок: {article_title[:80]}...")
            print(f"Контент: {len(article_content) if article_content else 0} символов")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Ошибка БД после {elapsed:.2f}s: {e}")
        return False

    print("\n📝 Шаг 2: Инициализируем AI сервис")
    print("-" * 60)

    try:
        ai_service = AIService()
        print("✅ AI сервис инициализирован")
    except Exception as e:
        print(f"❌ Ошибка инициализации AI: {e}")
        return False

    print("\n📝 Шаг 3: Генерируем выжимку через AI")
    print("-" * 60)

    ai_start_time = time.time()

    try:
        print("⏳ Отправляем запрос к AI... (это может занять 10-30 секунд)")

        summary, metrics = await ai_service.summarize_article(
            article_content=article_content,
            article_title=article_title,
            project=ProjectType.GYNECOLOGY
        )

        elapsed = time.time() - ai_start_time
        print(f"✅ Выжимка сгенерирована за {elapsed:.2f}s")
        print(f"Модель: {metrics.get('model_used')}")
        print(f"Токены: {metrics.get('tokens_used')}")
        print(f"\n📄 Выжимка (первые 200 символов):")
        print(summary.summary[:200] + "...")
        print(f"\n📊 Факты: {len(summary.facts)} шт.")

        total_time = time.time() - start_time
        print(f"\n⏱️ ОБЩЕЕ ВРЕМЯ: {total_time:.2f}s")

        if total_time > 60:
            print("⚠️ ВНИМАНИЕ: Время выполнения превысило 60 секунд!")
            print("   Это вызовет timeout в production!")

        return True

    except Exception as e:
        elapsed = time.time() - ai_start_time
        total_time = time.time() - start_time
        print(f"❌ Ошибка AI после {elapsed:.2f}s: {e}")
        print(f"⏱️ Общее время до ошибки: {total_time:.2f}s")

        import traceback
        traceback.print_exc()
        return False


async def main():
    """Запуск теста"""

    result = await test_summarize_endpoint()

    print("\n" + "=" * 60)
    if result:
        print("✅ ТЕСТ ПРОЙДЕН - генерация выжимки работает!")
    else:
        print("❌ ТЕСТ ПРОВАЛЕН - обнаружены проблемы!")
    print("=" * 60)

    return 0 if result else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
