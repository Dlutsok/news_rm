#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API настроек
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import httpx
import asyncio
from models.schemas import BitrixProjectSettingsCreate

async def test_api():
    """Тестирование API"""
    base_url = "http://localhost:8000"

    print("🔍 Тестирование API настроек...")

    async with httpx.AsyncClient() as client:
        # Тест 1: Получение всех настроек (без аутентификации)
        print("\n1️⃣ Тест получения всех настроек...")
        try:
            response = await client.get(f"{base_url}/api/settings/all")
            print(f"Status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error: {response.text}")
            else:
                print("✅ Получение настроек работает")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

        # Тест 2: Получение Bitrix проектов
        print("\n2️⃣ Тест получения Bitrix проектов...")
        try:
            response = await client.get(f"{base_url}/api/settings/bitrix-projects")
            print(f"Status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error: {response.text}")
            else:
                data = response.json()
                print(f"✅ Получено проектов: {len(data)}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

        # Тест 3: Создание проекта (без токена - должно вернуть 401)
        print("\n3️⃣ Тест создания проекта без токена...")
        test_project = {
            "project_code": "TEST2",
            "project_name": "test2.site",
            "display_name": "Тестовый проект 2",
            "api_url": "http://test2.com/api",
            "api_token": "test_token_2",
            "iblock_id": 38,
            "description": "Тестовый проект 2"
        }

        try:
            response = await client.post(
                f"{base_url}/api/settings/bitrix-projects",
                json=test_project
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code == 401:
                print("✅ Правильно требует авторизацию")
            elif response.status_code == 500:
                print("❌ Ошибка 500 - проблема на сервере")
            else:
                print(f"❓ Неожиданный статус: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

        # Тест 4: Создание проекта с токеном
        print("\n4️⃣ Тест создания проекта с токеном...")
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1ODE0MDQ4MX0.U0YF1djcub5CxQFS_z0AEtsrhWcNGK71CAcN8O4OI3M"

        try:
            response = await client.post(
                f"{base_url}/api/settings/bitrix-projects",
                json=test_project,
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code == 201:
                print("✅ Проект создан успешно")
            elif response.status_code == 400:
                print("❌ Ошибка валидации")
            elif response.status_code == 500:
                print("❌ Ошибка 500 - проблема на сервере")
            else:
                print(f"❓ Неожиданный статус: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

        # Тест 5: Обновление проекта (PUT)
        print("\n5️⃣ Тест обновления проекта...")
        update_data = {
            "display_name": "Обновленный тестовый проект",
            "description": "Обновленное описание"
        }

        try:
            response = await client.put(
                f"{base_url}/api/settings/bitrix-projects/TEST2",
                json=update_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Проект обновлен: {data.get('display_name')}")
            else:
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

        # Тест 6: Удаление проекта (DELETE)
        print("\n6️⃣ Тест удаления проекта...")
        try:
            response = await client.delete(
                f"{base_url}/api/settings/bitrix-projects/TEST2",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Проект удален успешно")
            else:
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())