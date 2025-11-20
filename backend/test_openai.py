#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы OpenAI API
"""

import os
import sys
import time
import httpx
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

API_KEY = os.getenv('OPENAI_API_KEY')
PROXY_URL = os.getenv('OPENAI_PROXY_URL')

print("=" * 60)
print("🧪 Тестирование OpenAI API")
print("=" * 60)
print(f"API Key: {'✅ Найден' if API_KEY else '❌ НЕ найден'}")
print(f"Proxy: {'✅ ' + PROXY_URL[:30] + '...' if PROXY_URL else '❌ НЕ настроен'}")
print("=" * 60)

if not API_KEY:
    print("❌ OPENAI_API_KEY не найден в .env файле!")
    sys.exit(1)


async def test_openai_simple():
    """Простой тест с минимальным промптом"""
    print("\n📝 Тест 1: Простой запрос к OpenAI API")
    print("-" * 60)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Say 'Hello, world!' in one word."}
        ],
        "max_tokens": 10,
        "temperature": 0.5
    }

    client_kwargs = {"timeout": httpx.Timeout(30.0)}
    if PROXY_URL:
        client_kwargs['proxies'] = PROXY_URL
        print(f"🔗 Используется прокси")

    start_time = time.time()

    try:
        async with httpx.AsyncClient(**client_kwargs) as client:
            print(f"⏳ Отправляем запрос... (timeout: 30s)")
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )

            elapsed = time.time() - start_time
            print(f"✅ Ответ получен за {elapsed:.2f}s")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                print(f"📤 Ответ: {content}")
                print(f"🎫 Токены: {tokens}")
                return True
            else:
                print(f"❌ Ошибка: {response.status_code}")
                print(f"📄 Тело ответа: {response.text}")
                return False

    except httpx.TimeoutException as e:
        elapsed = time.time() - start_time
        print(f"⏱️ TIMEOUT после {elapsed:.2f}s")
        print(f"❌ Ошибка: {str(e)}")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Ошибка после {elapsed:.2f}s: {str(e)}")
        return False


async def test_openai_summarize():
    """Тест с запросом похожим на summarize_article"""
    print("\n📝 Тест 2: Запрос генерации выжимки (как в production)")
    print("-" * 60)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "Ты медицинский редактор. Создай краткую выжимку статьи."
            },
            {
                "role": "user",
                "content": "Заголовок: Новое исследование о влиянии витамина D\n\nТекст: Ученые провели исследование влияния витамина D на здоровье. Результаты показали положительный эффект.\n\nСоздай JSON с полями summary и facts."
            }
        ],
        "max_tokens": 500,
        "temperature": 0.3
    }

    client_kwargs = {"timeout": httpx.Timeout(60.0)}
    if PROXY_URL:
        client_kwargs['proxies'] = PROXY_URL
        print(f"🔗 Используется прокси")

    start_time = time.time()

    try:
        async with httpx.AsyncClient(**client_kwargs) as client:
            print(f"⏳ Отправляем запрос... (timeout: 60s)")
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )

            elapsed = time.time() - start_time
            print(f"✅ Ответ получен за {elapsed:.2f}s")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                print(f"📤 Ответ (первые 200 символов): {content[:200]}...")
                print(f"🎫 Токены: {tokens}")
                return True
            else:
                print(f"❌ Ошибка: {response.status_code}")
                print(f"📄 Тело ответа: {response.text}")
                return False

    except httpx.TimeoutException as e:
        elapsed = time.time() - start_time
        print(f"⏱️ TIMEOUT после {elapsed:.2f}s")
        print(f"❌ Ошибка: {str(e)}")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Ошибка после {elapsed:.2f}s: {str(e)}")
        return False


async def main():
    """Запуск всех тестов"""

    # Тест 1: Простой запрос
    test1_result = await test_openai_simple()

    # Небольшая пауза между тестами
    await asyncio.sleep(2)

    # Тест 2: Запрос выжимки
    test2_result = await test_openai_summarize()

    # Результаты
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    print(f"Тест 1 (простой запрос): {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Тест 2 (выжимка статьи): {'✅ PASSED' if test2_result else '❌ FAILED'}")
    print("=" * 60)

    if test1_result and test2_result:
        print("\n✅ Все тесты пройдены! OpenAI API работает корректно.")
        return 0
    else:
        print("\n❌ Некоторые тесты провалились. Проверьте логи выше.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
