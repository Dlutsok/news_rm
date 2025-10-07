"""
Тестовый скрипт для проверки URL парсера и генерации статей
"""

import asyncio
from services.url_article_parser import url_parser
from database.schemas import ProjectType

# Тестовые медицинские URL
TEST_URLS = [
    "https://medscape.com/viewarticle/1000000",  # Пример медицинского ресурса
    "https://www.sciencedaily.com/releases/2024/01/240101000000.htm",  # Научные новости
    "https://pubmed.ncbi.nlm.nih.gov/",  # PubMed
]

async def test_parse_single_url():
    """Тест парсинга одного URL"""
    test_url = "https://news.ycombinator.com/"  # Простой URL для теста

    print(f"🔍 Тестирование парсинга URL: {test_url}")
    print("-" * 80)

    async with url_parser:
        result = await url_parser.parse_article(test_url)

        if result['success']:
            print(f"✅ Успешно распарсено!")
            print(f"📊 URL: {result['url']}")
            print(f"🌐 Домен: {result['domain']}")
            print(f"📝 Длина контента: {len(result['content'])} символов")
            print(f"📄 Первые 500 символов:")
            print(result['content'][:500])
            print("...")
        else:
            print(f"❌ Ошибка парсинга: {result['error']}")

    print("-" * 80)

async def test_parse_multiple_urls():
    """Тест парсинга нескольких URL параллельно"""
    test_urls = [
        "https://news.ycombinator.com/",
        "https://github.com/",
        "https://stackoverflow.com/"
    ]

    print(f"🔍 Тестирование парсинга {len(test_urls)} URL параллельно")
    print("-" * 80)

    async with url_parser:
        results = await url_parser.parse_multiple_urls(test_urls)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['url']}")
            if result['success']:
                print(f"   ✅ Успех - {len(result['content'])} символов")
            else:
                print(f"   ❌ Ошибка: {result['error']}")

    print("-" * 80)

async def main():
    """Главная функция тестирования"""
    print("=" * 80)
    print("🧪 ТЕСТИРОВАНИЕ URL ARTICLE PARSER")
    print("=" * 80)
    print()

    # Тест 1: Парсинг одного URL
    await test_parse_single_url()
    print()

    # Тест 2: Парсинг нескольких URL
    await test_parse_multiple_urls()
    print()

    print("=" * 80)
    print("✅ Все тесты завершены!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
