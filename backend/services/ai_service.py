"""
Сервис для работы с AI моделями (OpenAI GPT-3.5 и GPT-4o)
"""

import json
import re
import time
import logging
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
from models.schemas import ArticleSummary, GeneratedArticle, ProjectType
from pydantic import BaseModel
from core.config import settings
from services.settings_service import settings_service
from services.ai_provider import get_openai_provider

logger = logging.getLogger(__name__)


class TelegramPostSettings(BaseModel):
    hook_type: str = "question"  # question, shocking_fact, statistics, contradiction
    disclosure_level: str = "hint"  # hint, main_idea, almost_all
    call_to_action: str = "curiosity"  # curiosity, urgency, expertise
    includeImage: bool = True


class AIService:
    """Сервис для работы с AI моделями"""
    
    def __init__(self, api_key: str = None):
        # Используем новый провайдер с поддержкой прокси
        self.provider = get_openai_provider()
        
    async def summarize_article(self, article_content: str, article_title: str, project: ProjectType) -> Tuple[ArticleSummary, Dict]:
        """
        Создание ПОДРОБНОЙ выжимки статьи с помощью GPT-3.5-turbo-16k (до 1200 символов)
        
        Args:
            article_content: Полный текст статьи
            article_title: Заголовок статьи
            project: Тип проекта для адаптации
            
        Returns:
            Tuple[ArticleSummary, Dict]: Подробная выжимка (до 1200 символов) с максимумом фактов и метрики
        """
        start_time = time.time()
        
        # Определяем специализацию для проекта
        project_specialization = {
            ProjectType.GYNECOLOGY: "гинекологии и женского здоровья",
            ProjectType.THERAPY: "терапии и общей медицины", 
            ProjectType.PEDIATRICS: "педиатрии и детского здоровья"
        }
        
        specialization = project_specialization.get(project, "медицины")
        
        system_prompt = f"""Ты — опытный медицинский редактор с 10-летним стажем, специализирующийся на {specialization}.

🚨 КРИТИЧЕСКАЯ ЗАДАЧА: Создай МАКСИМАЛЬНО ИНФОРМАТИВНУЮ выжимку для последующей генерации профессиональной медицинской статьи!

📋 ОБЯЗАТЕЛЬНЫЕ ТРЕБОВАНИЯ:
1. 🔍 **Сохрани ВСЕ ключевые детали**: точные даты, время, цифры, имена, должности
2. 🏥 **Медицинская точность**: диагнозы, симптомы, степень тяжести, клинические данные
3. 📊 **Статистика и факты**: количество пострадавших, возрастные группы, сроки лечения
4. 🏛️ **Официальные источники**: названия ведомств, учреждений, экспертов
5. ⚖️ **Правовые аспекты**: статьи законов, процедуры, ответственные лица
6. 🌍 **Контекст события**: масштаб, география, предыстория

🎯 ЦЕЛЬ: Выжимка должна содержать ВСЮ информацию для создания профессиональной медицинской статьи объемом 2500+ символов!

⚠️ ПРИНЦИП: Лучше больше деталей, чем меньше! Каждый факт может стать важным разделом статьи.

Верни результат СТРОГО в формате JSON, без комментариев:
{{
  "summary": "МАКСИМАЛЬНО ПОДРОБНАЯ выжимка (4-6 абзацев, до 1500 символов с ВСЕМИ важными деталями)",
  "facts": [
    "Детальный факт 1 с цифрами/именами",
    "Детальный факт 2 с контекстом",
    "Детальный факт 3 со статистикой",
    "Детальный факт 4",
    "Детальный факт 5",
    "Детальный факт 6",
    "Детальный факт 7"
  ]
}}

Пример:
{{
  "summary": "Российские ученые из НИИ Склифосовского и РНИМУ им. Пирогова провели масштабное исследование влияния загрязненного воздуха на развитие менингиомы. В исследовании приняли участие 15,000 пациентов из Москвы и Санкт-Петербурга в период с 2018 по 2023 год. Результаты показали, что длительное воздействие ультрадисперсных частиц PM2.5 увеличивает риск развития менингиомы на 40%. Особенно опасным оказалось воздействие диоксида азота от автомобильного транспорта.",
  "facts": [
    "Исследование проводили НИИ Склифосовского и РНИМУ им. Пирогова",
    "В исследовании участвовали 15,000 пациентов",
    "Период исследования: 2018-2023 годы",
    "Риск менингиомы увеличивается на 40% при воздействии PM2.5",
    "Диоксид азота от транспорта особенно опасен",
    "Исследование охватило Москву и Санкт-Петербург",
    "Изучались ультрадисперсные частицы и элементарный углерод"
  ]
}}"""

        # Генерационный маркер уникальности — помогает добиваться разнообразия ответов
        generation_marker = str(uuid4())

        user_prompt = f"""Заголовок: {article_title}

Текст статьи:
{article_content}

🎯 ЗАДАЧА: Создай ПОДРОБНУЮ выжимку для проекта {project.value}.
⚠️ ВАЖНО: Включи все важные детали, цифры, имена, даты — из этой выжимки будет создаваться полная новость 2000+ символов!
📊 МАКСИМУМ фактов и контекста!

Технический маркер уникальности (НЕ включай его в ответ и не упоминай): {generation_marker}
"""

        try:
            # Настройки модели для выжимки из системных настроек
            try:
                summary_model_setting = settings_service.get_app_setting("openai_summary_model")
                summary_model_name = (summary_model_setting.setting_value if summary_model_setting and summary_model_setting.setting_value else "gpt-4o")

                summary_temperature_setting = settings_service.get_app_setting("openai_summary_temperature")
                summary_temperature_value = float(summary_temperature_setting.setting_value) if summary_temperature_setting and summary_temperature_setting.setting_value else 0.3

                summary_max_tokens_setting = settings_service.get_app_setting("openai_summary_max_tokens")
                summary_max_tokens_value = int(summary_max_tokens_setting.setting_value) if summary_max_tokens_setting and summary_max_tokens_setting.setting_value else 1500
            except Exception:
                # На случай проблем с доступом к настройкам
                summary_model_name = "gpt-4o"
                summary_temperature_value = 0.3
                summary_max_tokens_value = 1500

            # Пытаемся использовать выбранную модель, с безопасным фолбэком при отсутствии доступа
            preferred_order = [summary_model_name, "gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo-16k"]
            # Убираем дубликаты, сохраняя порядок
            seen = set()
            summary_model_candidates = []
            for m in preferred_order:
                if m and m not in seen:
                    seen.add(m)
                    summary_model_candidates.append(m)

            last_error = None
            used_summary_model = summary_model_name
            response = None
            for candidate in summary_model_candidates:
                try:
                    response = await self.provider.get_completion(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        model=candidate,
                        temperature=summary_temperature_value,
                        max_tokens=summary_max_tokens_value,
                        top_p=0.95
                    )
                    used_summary_model = candidate
                    break
                except Exception as e:
                    last_error = e
                    # Продолжаем попытки при неактивной/недоступной модели
                    err_msg = str(e).lower()
                    if "model_not_found" in err_msg or "404" in err_msg:
                        continue
                    # Иные ошибки пробрасываем
                    raise
            if response is None:
                # Если все кандидаты провалились — бросаем последнюю ошибку
                raise last_error or Exception("No available model for summarize")
            
            # Извлекаем JSON из ответа
            content = response["content"].strip()
            
            # Пытаемся найти JSON в ответе
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()

            # Парсинг JSON с обработкой ошибок
            try:
                result_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Response content: {content}")

                # Попытка исправить JSON
                try:
                    fixed_content = re.sub(r'"\s*\n\s*"', '",\n  "', content)
                    fixed_content = re.sub(r'}\s*\n\s*"', '},\n  "', fixed_content)
                    fixed_content = re.sub(r']\s*\n\s*"', '],\n  "', fixed_content)

                    # Добавляем закрывающую скобку если отсутствует
                    fixed_content = fixed_content.strip()
                    if not fixed_content.endswith('}'):
                        fixed_content += '\n}'
                        logger.info("Added missing closing brace to JSON")

                    result_data = json.loads(fixed_content)
                    logger.info("Successfully fixed JSON in summarize_article")
                except json.JSONDecodeError:
                    raise Exception(f"Ошибка парсинга ответа AI: {str(e)}")

            # Создаем объект ArticleSummary
            summary = ArticleSummary(
                summary=result_data["summary"],
                facts=result_data["facts"]
            )
            
            # Метрики
            processing_time = time.time() - start_time
            metrics = {
                "model_used": used_summary_model,
                "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                "processing_time_seconds": processing_time,
                "success": True
            }
            
            logger.info(f"Article summarized successfully. Tokens: {response.get('usage', {}).get('total_tokens', 0)}, Time: {processing_time:.2f}s")

            return summary, metrics

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error in summarize_article: {e}")
            
            metrics = {
                "model_used": "gpt-3.5-turbo-16k",
                "tokens_used": 0,
                "processing_time_seconds": processing_time,
                "success": False,
                "error": str(e)
            }
            
            raise Exception(f"Ошибка при сжатии статьи: {str(e)}")

    async def generate_telegram_post_for_published(
        self,
        news_data: Dict,  # Данные опубликованной новости
        settings: Optional[TelegramPostSettings] = None
    ) -> Tuple[str, Dict]:
        """
        Генерация Telegram поста для опубликованной новости.
        Использует финальный текст статьи и URL опубликованной новости.
        """
        start_time = time.time()

        # Устанавливаем настройки по умолчанию, если не переданы
        if settings is None:
            settings = TelegramPostSettings()

        try:
            # Извлекаем данные из опубликованной новости
            article_title = news_data.get("seo_title", "") or news_data.get("title", "")
            published_url = news_data.get("published_url", "")  # URL опубликованной статьи
            news_text = news_data.get("news_text", "")
            project = ProjectType(news_data.get("project", "therapy"))

            # Создаем краткую выжимку из опубликованного текста для генерации поста
            # Берем первые 800 символов и ключевые предложения
            summary_for_post = self._extract_key_info_from_published_text(news_text)

            # Имитируем facts из важных моментов статьи
            facts = self._extract_facts_from_published_text(news_text)

            # Определяем стратегию интриги по настройкам
            hook_strategies = {
                "question": {
                    "approach": "Начни с провокационного вопроса",
                    "examples": ["А знали ли вы, что...", "Что если бы вам сказали...", "Почему врачи не говорят о..."]
                },
                "shocking_fact": {
                    "approach": "Начни с неожиданного факта",
                    "examples": ["85% людей не знают о...", "Новое исследование шокировало экспертов...", "То, что обнаружили ученые..."]
                },
                "statistics": {
                    "approach": "Начни с впечатляющей статистики",
                    "examples": ["Каждая 3-я женщина сталкивается с...", "В 90% случаев врачи не замечают...", "За последний год число случаев..."]
                },
                "contradiction": {
                    "approach": "Начни с развенчания мифа",
                    "examples": ["Вопреки общему мнению...", "То, что считалось безопасным...", "Оказывается, все это время мы ошибались..."]
                }
            }
            hook_strategy = hook_strategies.get(settings.hook_type, hook_strategies["question"])

            disclosure_levels = {
                "hint": {
                    "instruction": "Дай только намек на суть, создай максимальное любопытство",
                    "detail": "Упомяни проблему/открытие, но НЕ раскрывай решение или результат"
                },
                "main_idea": {
                    "instruction": "Раскрой основную идею, но скрой детали и выводы",
                    "detail": "Объясни суть проблемы/исследования, но оставь интригу о результатах"
                },
                "almost_all": {
                    "instruction": "Расскажи почти всё, но скрой самое важное - итоговые выводы",
                    "detail": "Дай полный контекст и даже некоторые результаты, но финальные выводы/рекомендации остаются за кадром"
                }
            }
            disclosure_level = disclosure_levels.get(settings.disclosure_level, disclosure_levels["hint"])

            cta_styles = {
                "curiosity": {
                    "phrase": "Подробности →",
                    "tone": "Мягкий призыв через любопытство"
                },
                "urgency": {
                    "phrase": "Читать сейчас →",
                    "tone": "Подчеркивание важности и срочности"
                },
                "expertise": {
                    "phrase": "Узнать больше →",
                    "tone": "Экспертный подход, фокус на знаниях"
                }
            }
            cta_style = cta_styles.get(settings.call_to_action, cta_styles["curiosity"])

            system_prompt = f"""Ты — опытный СММ-специалист медицинского издания, мастер создания ИНТРИГУЮЩИХ анонсов для Telegram.

🎯 ГЛАВНАЯ ЦЕЛЬ: Создать пост, который заставит читателя перейти на сайт за полной информацией!

📋 СТРАТЕГИЯ ИНТРИГИ:
{hook_strategy['approach']}
Примеры зацепок: {hook_strategy['examples']}

🔍 УРОВЕНЬ РАСКРЫТИЯ:
{disclosure_level['instruction']}
Детали: {disclosure_level['detail']}

✨ СТРУКТУРА ПРОФЕССИОНАЛЬНОГО ПОСТА:
🏷️ **МИНИ-ЗАГОЛОВОК** (1 строка): Краткое название темы в жирном шрифте (*текст*)

🔥 **КРЮЧОК** (1-2 предложения): {hook_strategy['approach']}

📋 **КОНТЕКСТ** (1-2 предложения): Минимум информации для понимания темы

❓ **ИНТРИГА** (1-2 предложения): Намек на важную информацию БЕЗ её раскрытия

🔗 **ПРИЗЫВ**: "{cta_style['phrase']}"

📏 ТРЕБОВАНИЯ К ФОРМАТИРОВАНИЮ:
- Используй переносы строк между блоками для читабельности
- Жирный шрифт (*текст*) для мини-заголовка и ключевых акцентов
- Пустая строка между каждым блоком информации
- 1-2 медицинских эмодзи в начале: 🩺🧬💊🔬🧪📊🫀🧠
- Общая длина: 300-450 символов (включая форматирование и переносы)
- Создавать НЕДОСКАЗАННОСТЬ - главный принцип!
- НЕ давать полные ответы и решения в посте

🚫 СТРОГО ЗАПРЕЩЕНО:
- Полное раскрытие сути новости
- Конкретные выводы и рекомендации
- HTML/Markdown разметка
- Слова "читайте", "подробнее", "больше информации" (используй только призыв в конце)

✅ ОБЯЗАТЕЛЬНО:
- Заканчивать призывом "{cta_style['phrase']}"
- Оставлять читателя с вопросами
- Создавать ощущение упущенной выгоды, если не перейдет
- Естественно встроить ссылку в текст (не отдельной строкой!)
- Использовать переносы строк для структурирования"""

            facts_text = "\n".join([f"• {f}" for f in (facts or [])[:3]])  # Ограничиваем 3 самыми важными фактами
            user_prompt = (
                f"ИСТОЧНИК ДЛЯ ИНТРИГУЮЩЕГО АНОНСА:\n"
                f"Заголовок статьи: {article_title}\n\n"
                f"Суть опубликованного материала: {summary_for_post}\n\n"
                f"Ключевые факты:\n{facts_text}\n\n"
                f"🎯 ЗАДАЧА: Создай ИНТРИГУЮЩИЙ анонс опубликованной статьи!\n\n"
                f"📋 НАСТРОЙКИ ИНТРИГИ:\n"
                f"• Тип зацепки: {hook_strategy['approach'].lower()}\n"
                f"• Уровень раскрытия: {disclosure_level['instruction'].lower()}\n"
                f"• Призыв к действию: {cta_style['tone'].lower()}\n\n"
                f"⚠️ ПОМНИ: НЕ раскрывай полную суть! Читатель должен захотеть перейти за подробностями!\n"
                f"✅ Обязательно заверши пост фразой: \"{cta_style['phrase']}\"\n"
                f"🔗 ВАЖНО: НЕ добавляй никаких ссылок в текст! Заканчивай только призывом к действию."
            )

            # Читаем модель из настроек с фолбэком к gpt-4o-mini
            try:
                summary_model_setting = settings_service.get_app_setting("openai_summary_model")
                model_name = (
                    summary_model_setting.setting_value
                    if summary_model_setting and summary_model_setting.setting_value
                    else "gpt-4o-mini"
                )
            except Exception:
                model_name = "gpt-4o-mini"

            preferred_order = [model_name, "gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo-16k"]
            seen = set()
            candidates = []
            for m in preferred_order:
                if m and m not in seen:
                    seen.add(m)
                    candidates.append(m)

            last_error = None
            used_model = model_name
            response = None
            for candidate in candidates:
                try:
                    response = await self.provider.get_completion(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        model=candidate,
                        temperature=0.6,
                        max_tokens=500,
                        top_p=0.95,
                    )
                    used_model = candidate
                    break
                except Exception as e:
                    last_error = e
                    err_msg = str(e).lower()
                    if "model_not_found" in err_msg or "404" in err_msg:
                        continue
                    raise
            if response is None:
                raise last_error or Exception("No available model for telegram post")

            content = (response.get("content", "") or "").strip()
            # Обрезаем по длине для интригующих постов (200-350 символов)
            max_length = 350
            if len(content) > max_length:
                content = content[:max_length].rstrip() + "…"

            processing_time = time.time() - start_time
            metrics = {
                "model_used": used_model,
                "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                "processing_time_seconds": processing_time,
                "success": True,
            }
            return content, metrics

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error in generate_telegram_post_for_published: {e}")
            metrics = {
                "model_used": locals().get("model_name", "gpt-4o-mini"),
                "tokens_used": 0,
                "processing_time_seconds": processing_time,
                "success": False,
                "error": str(e),
            }
            # Фолбэк: простой анонс
            fallback = f"🩺 Новая статья на нашем сайте!\n\n{cta_style['phrase']}"
            if published_url:
                fallback = f"{fallback}\n{published_url}"
            return fallback, metrics

    def _extract_key_info_from_published_text(self, news_text: str) -> str:
        """Извлекает ключевую информацию из опубликованного текста для создания краткой выжимки."""
        if not news_text:
            return ""

        # Убираем HTML теги для анализа
        import re
        clean_text = re.sub(r'<[^>]+>', ' ', news_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # Берем первые 800 символов как основу для выжимки
        summary = clean_text[:800] + ("..." if len(clean_text) > 800 else "")
        return summary

    def _extract_facts_from_published_text(self, news_text: str) -> List[str]:
        """Извлекает ключевые факты из опубликованного текста."""
        if not news_text:
            return []

        # Убираем HTML теги
        import re
        clean_text = re.sub(r'<[^>]+>', ' ', news_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # Простой анализ: ищем предложения с цифрами, датами, названиями
        sentences = clean_text.split('.')
        facts = []

        for sentence in sentences[:10]:  # Анализируем первые 10 предложений
            sentence = sentence.strip()
            if len(sentence) < 20:  # Пропускаем слишком короткие
                continue

            # Предложения с цифрами, процентами, годами часто содержат факты
            if re.search(r'\d+[%]?|\d{4}|\d+\s*[а-я]+', sentence):
                facts.append(sentence)
            # Предложения с ключевыми словами
            elif any(keyword in sentence.lower() for keyword in ['исследование', 'ученые', 'врачи', 'пациент', 'результат', 'данные']):
                facts.append(sentence)

            if len(facts) >= 5:  # Ограничиваем количество фактов
                break

        return facts[:5]  # Возвращаем максимум 5 фактов

    async def generate_telegram_post(
        self,
        article_title: str,
        article_url: Optional[str],
        summary: str,
        facts: List[str],
        project: ProjectType,
        settings: Optional[TelegramPostSettings] = None
    ) -> Tuple[str, Dict]:
        """
        Генерация короткого анонса для Telegram на основе выжимки и фактов.
        Требования: интрига, лаконично, 180–400 символов, ссылка в конце.
        Использует GPT-5-mini с фолбэком.
        """
        start_time = time.time()

        # Устанавливаем настройки по умолчанию, если не переданы
        if settings is None:
            settings = TelegramPostSettings()

        try:
            # Определяем стратегию интриги по настройкам
            hook_strategies = {
                "question": {
                    "approach": "Начни с провокационного вопроса",
                    "examples": ["А знали ли вы, что...", "Что если бы вам сказали...", "Почему врачи не говорят о..."]
                },
                "shocking_fact": {
                    "approach": "Начни с неожиданного факта",
                    "examples": ["85% людей не знают о...", "Новое исследование шокировало экспертов...", "То, что обнаружили ученые..."]
                },
                "statistics": {
                    "approach": "Начни с впечатляющей статистики",
                    "examples": ["Каждая 3-я женщина сталкивается с...", "В 90% случаев врачи не замечают...", "За последний год число случаев..."]
                },
                "contradiction": {
                    "approach": "Начни с развенчания мифа",
                    "examples": ["Вопреки общему мнению...", "То, что считалось безопасным...", "Оказывается, все это время мы ошибались..."]
                }
            }
            hook_strategy = hook_strategies.get(settings.hook_type, hook_strategies["question"])

            disclosure_levels = {
                "hint": {
                    "instruction": "Дай только намек на суть, создай максимальное любопытство",
                    "detail": "Упомяни проблему/открытие, но НЕ раскрывай решение или результат"
                },
                "main_idea": {
                    "instruction": "Раскрой основную идею, но скрой детали и выводы",
                    "detail": "Объясни суть проблемы/исследования, но оставь интригу о результатах"
                },
                "almost_all": {
                    "instruction": "Расскажи почти всё, но скрой самое важное - итоговые выводы",
                    "detail": "Дай полный контекст и даже некоторые результаты, но финальные выводы/рекомендации остаются за кадром"
                }
            }
            disclosure_level = disclosure_levels.get(settings.disclosure_level, disclosure_levels["hint"])

            cta_styles = {
                "curiosity": {
                    "phrase": "Подробности →",
                    "tone": "Мягкий призыв через любопытство"
                },
                "urgency": {
                    "phrase": "Читать сейчас →",
                    "tone": "Подчеркивание важности и срочности"
                },
                "expertise": {
                    "phrase": "Узнать больше →",
                    "tone": "Экспертный подход, фокус на знаниях"
                }
            }
            cta_style = cta_styles.get(settings.call_to_action, cta_styles["curiosity"])

            system_prompt = f"""Ты — опытный СММ-специалист медицинского издания, мастер создания ИНТРИГУЮЩИХ анонсов для Telegram.

🎯 ГЛАВНАЯ ЦЕЛЬ: Создать пост, который заставит читателя перейти на сайт за полной информацией!

📋 СТРАТЕГИЯ ИНТРИГИ:
{hook_strategy['approach']}
Примеры зацепок: {hook_strategy['example']}

🔍 УРОВЕНЬ РАСКРЫТИЯ:
{disclosure_level['instruction']}
Детали: {disclosure_level['detail']}

✨ СТРУКТУРА ИНТРИГУЮЩЕГО ПОСТА:
1️⃣ КРЮЧОК (1-2 предложения): {hook_strategy['approach']}
2️⃣ КОНТЕКСТ (1-2 предложения): Минимум информации для понимания темы
3️⃣ ИНТРИГА (1-2 предложения): Намек на важную информацию БЕЗ её раскрытия
4️⃣ ПРИЗЫВ (1 строка): "{cta_style['phrase']}"

📏 ТРЕБОВАНИЯ:
- Длина: 200-350 символов (включая эмодзи и призыв)
- 1-2 медицинских эмодзи в начале: 🩺🧬💊🔬🧪📊🫀🧠
- Создавать НЕДОСКАЗАННОСТЬ - главный принцип!
- НЕ давать полные ответы и решения в посте

🚫 СТРОГО ЗАПРЕЩЕНО:
- Полное раскрытие сути новости
- Конкретные выводы и рекомендации
- HTML/Markdown разметка
- Слова "читайте", "подробнее", "больше информации" (используй только призыв в конце)

✅ ОБЯЗАТЕЛЬНО:
- Заканчивать призывом "{cta_style['phrase']}"
- Оставлять читателя с вопросами
- Создавать ощущение упущенной выгоды, если не перейдет"""

            facts_text = "\n".join([f"• {f}" for f in (facts or [])[:3]])  # Ограничиваем 3 самыми важными фактами
            user_prompt = (
                f"ИСТОЧНИК ДЛЯ ИНТРИГУЮЩЕГО АНОНСА:\n"
                f"Заголовок статьи: {article_title}\n\n"
                f"Суть материала: {summary}\n\n"
                f"Ключевые факты:\n{facts_text}\n\n"
                f"🎯 ЗАДАЧА: Создай ИНТРИГУЮЩИЙ анонс, который заставит перейти на сайт!\n\n"
                f"📋 НАСТРОЙКИ ИНТРИГИ:\n"
                f"• Тип зацепки: {hook_strategy['approach'].lower()}\n"
                f"• Уровень раскрытия: {disclosure_level['instruction'].lower()}\n"
                f"• Призыв к действию: {cta_style['tone'].lower()}\n\n"
                f"⚠️ ПОМНИ: НЕ раскрывай полную суть! Читатель должен захотеть перейти за подробностями!\n"
                f"✅ Обязательно заверши постом фразой: \"{cta_style['phrase']}\""
            )

            # Читаем модель из настроек с фолбэком к gpt-4o-mini
            try:
                summary_model_setting = settings_service.get_app_setting("openai_summary_model")
                model_name = (
                    summary_model_setting.setting_value
                    if summary_model_setting and summary_model_setting.setting_value
                    else "gpt-4o-mini"
                )
            except Exception:
                model_name = "gpt-4o-mini"

            preferred_order = [model_name, "gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo-16k"]
            seen = set()
            candidates = []
            for m in preferred_order:
                if m and m not in seen:
                    seen.add(m)
                    candidates.append(m)

            last_error = None
            used_model = model_name
            response = None
            for candidate in candidates:
                try:
                    response = await self.provider.get_completion(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        model=candidate,
                        temperature=0.6,
                        max_tokens=500,
                        top_p=0.95,
                    )
                    used_model = candidate
                    break
                except Exception as e:
                    last_error = e
                    err_msg = str(e).lower()
                    if "model_not_found" in err_msg or "404" in err_msg:
                        continue
                    raise
            if response is None:
                raise last_error or Exception("No available model for telegram post")

            content = (response.get("content", "") or "").strip()
            # Обрезаем по длине для интригующих постов (200-350 символов)
            max_length = 350
            if len(content) > max_length:
                content = content[:max_length].rstrip() + "…"
            if article_url and (article_url not in content):
                separator = "\n— " if "\n" not in content[-4:] else "— "
                content = f"{content}{separator}{article_url}"

            processing_time = time.time() - start_time
            metrics = {
                "model_used": used_model,
                "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                "processing_time_seconds": processing_time,
                "success": True,
            }
            return content, metrics

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error in generate_telegram_post: {e}")
            metrics = {
                "model_used": locals().get("model_name", "gpt-4o-mini"),
                "tokens_used": 0,
                "processing_time_seconds": processing_time,
                "success": False,
                "error": str(e),
            }
            # Фолбэк: простой анонс
            fallback = (summary or "").strip()
            fallback = (fallback[:380] + "…") if len(fallback) > 380 else fallback
            if article_url:
                fallback = f"{fallback}\n— {article_url}"
            return fallback, metrics

    async def clean_article_content(self, raw_content: str, source_url: str, max_retries: int = 3) -> Tuple[str, Dict]:
        """
        🧹 Очистка статьи от навигации, рекламы, футеров через GPT-4o mini
        Включает retry механизм (3 попытки) и валидацию результата.

        Args:
            raw_content: Сырой контент после парсинга (Jina AI / trafilatura)
            source_url: URL источника для контекста
            max_retries: Максимальное количество попыток при ошибках (по умолчанию 3)

        Returns:
            Tuple[str, Dict]: Очищенный контент и метрики
        """
        start_time = time.time()
        last_error = None
        
        # Ограничиваем размер контента для экономии токенов
        original_length = len(raw_content)
        if len(raw_content) > 30000:
            logger.warning(f"⚠️ Content too large ({len(raw_content)} chars), truncating to 30000")
            raw_content = raw_content[:30000]
        
        # 🔄 RETRY LOOP: пытаемся до max_retries раз
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    logger.warning(f"🔄 GPT cleaning retry attempt {attempt}/{max_retries}")
                    # Небольшая задержка между попытками
                    import asyncio
                    await asyncio.sleep(min(attempt * 2, 10))  # 2, 4, 6... секунд, макс 10
                
                logger.info(f"🧹 Cleaning article content via GPT-4o mini (attempt {attempt}), input length: {len(raw_content)} chars")

                system_prompt = """Ты — эксперт по очистке текста статей от служебной информации.

🎯 ЗАДАЧА: Извлечь ТОЛЬКО основной контент статьи, удалив всё лишнее.

❌ ОБЯЗАТЕЛЬНО УДАЛИ:
• Навигационные меню (Главная, О нас, Контакты, Мероприятия, Эксперты, Новости, Спецпроект)
• Футеры и копирайты (© 2024, Все права защищены, ООО, ИНН, ОГРН, ОКПО, Юридический адрес)
• Контактную информацию (Email, телефоны вида +7, WhatsApp, Telegram контакты)
• Модальные окна и уведомления ("Авторизоваться", "Вход", "Регистрация", "Подтвердите возраст", "зарегистрированных пользователей")
• Cookie banners и GDPR уведомления
• Рекламные блоки и баннеры
• Ссылки на социальные сети (VK, Telegram, Facebook, Twitter, WhatsApp и т.д.)
• Формы подписки и призывы подписаться ("Написать нам", "Подписаться на рассылку")
• Блоки "Читайте также", "Похожие статьи", "Популярные новости", "Ближайшие мероприятия"
• Служебную информацию (дата публикации отдельной строкой, автор отдельной строкой)
• Счетчики и метрики (количество просмотров, лайков, комментариев)
• Кнопки действий ("Читать далее", "Подробнее", "Поделиться", кнопки соцсетей)
• Теги и категории отдельными блоками (#новости, #медицина, Специальности)
• Хлебные крошки навигации (Главная > Новости > Статья)
• Повторяющиеся элементы навигации
• Информацию о компании/организации (Наименование организации, реквизиты)
• Пользовательские соглашения и оферты
• Блоки с ссылками на другие разделы сайта

✅ СОХРАНИ:
• Заголовок статьи (один главный H1)
• Весь основной текст статьи
• Подзаголовки (H2, H3)
• Списки, таблицы, цитаты (если они часть статьи)
• Медицинские термины, названия, даты и цифры из текста
• Ссылки на источники ВНУТРИ текста статьи (например, "Оригинальную версию статьи читайте на сайте")

📝 ФОРМАТ ВЫВОДА:
Верни очищенный текст в markdown формате. Структура:

# Заголовок статьи

Основной текст...

## Подзаголовок 1

Текст раздела...

⚠️ ВАЖНО:
- Не добавляй ничего от себя
- Не изменяй факты и формулировки
- Просто убери всё лишнее и оставь чистую статью
- Будь максимально строгим к удалению навигации, контактов, модальных окон
- Если видишь "Авторизоваться", "ИНН", "ОГРН", телефоны, email - УДАЛИ их полностью

📚 ПРИМЕРЫ ЧТО УДАЛЯТЬ:
BAD (удалить): "**** зарегистрированных пользователей"
BAD (удалить): "О нас | Mероприятия | Право на жизнь"
BAD (удалить): "ИНН: | ОГРН:"
BAD (удалить): "[email protected]"
BAD (удалить): "Подтвердите, что вы совершеннолетний"
BAD (удалить): "Наименование организации: ООО"
BAD (удалить): "ПОПУЛЯРНЫЕ НОВОСТИ" со списком ссылок
BAD (удалить): "Ближайшие мероприятия" со списком событий
BAD (удалить): "Написать нам | Условия использования | Оферта"

GOOD (сохранить): Заголовок и основной текст статьи с медицинской информацией"""

                user_prompt = f"""Очисти эту статью от навигации, рекламы и служебной информации.

Источник: {source_url}

Исходный текст:
{raw_content}

Верни только очищенный контент в markdown."""

                response = await self.provider.get_completion(
                    model="gpt-4o-mini",  # Быстро и дёшево
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0,  # Максимальная детерминированность для строгой очистки
                    max_tokens=8000
                )

                cleaned_content = response["content"].strip()
                processing_time = time.time() - start_time

                # ✅ ВАЛИДАЦИЯ РЕЗУЛЬТАТА: проверяем качество очистки
                validation_result = self._validate_cleaned_content(cleaned_content)
                
                metrics = {
                    "model_used": "gpt-4o-mini",
                    "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                    "processing_time_seconds": processing_time,
                    "input_length": original_length,
                    "output_length": len(cleaned_content),
                    "reduction_percent": round((1 - len(cleaned_content) / len(raw_content)) * 100, 1) if len(raw_content) > 0 else 0,
                    "attempt": attempt,
                    "validation_passed": validation_result["passed"],
                    "validation_warnings": validation_result["warnings"]
                }

                # Логируем результат валидации
                if not validation_result["passed"]:
                    logger.warning(f"⚠️ GPT cleaning validation FAILED: {', '.join(validation_result['warnings'])}")
                    logger.warning(f"🔍 Cleaned content preview (first 500 chars): {cleaned_content[:500]}")
                else:
                    logger.info(f"✅ Article cleaned via GPT-4o mini: {metrics['reduction_percent']}% reduction, {metrics['tokens_used']} tokens, {processing_time:.2f}s (attempt {attempt})")

                return cleaned_content, metrics

            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                logger.error(f"❌ Error cleaning article via GPT (attempt {attempt}/{max_retries}): {error_type} - {str(e)}")
                
                # Если это не последняя попытка - продолжаем retry
                if attempt < max_retries:
                    continue
        
        # 🔴 Все попытки исчерпаны - возвращаем fallback
        logger.error(f"🔴 GPT cleaning FAILED after {max_retries} attempts. Returning raw content as fallback.")
        logger.error(f"🔴 Last error: {type(last_error).__name__} - {str(last_error)}")
        
        # Fallback: возвращаем оригинальный контент
        metrics = {
            "model_used": "gpt-4o-mini",
            "tokens_used": 0,
            "processing_time_seconds": time.time() - start_time,
            "error": str(last_error),
            "error_type": type(last_error).__name__,
            "fallback": True,
            "attempts": max_retries,
            "validation_passed": False
        }
        return raw_content, metrics
    
    def _validate_cleaned_content(self, content: str) -> Dict:
        """
        ✅ Валидация очищенного контента - проверка что мусор действительно удалён.
        
        Args:
            content: Очищенный контент
            
        Returns:
            Dict: {"passed": bool, "warnings": List[str]}
        """
        warnings = []
        
        # Проверяем наличие типичного мусора (case-insensitive)
        content_lower = content.lower()
        
        garbage_patterns = [
            ("авторизоваться", "Найдено слово 'авторизоваться'"),
            ("авторизуйтесь", "Найдено слово 'авторизуйтесь'"),
            ("подтвердите возраст", "Найдено 'подтвердите возраст'"),
            ("зарегистрированных пользователей", "Найдено 'зарегистрированных пользователей'"),
            ("инн:", "Найдено 'ИНН:'"),
            ("огрн:", "Найдено 'ОГРН:'"),
            ("окпо:", "Найдено 'ОКПО:'"),
            ("юридический адрес", "Найдено 'юридический адрес'"),
            ("наименование организации", "Найдено 'наименование организации'"),
            ("популярные новости", "Найден блок 'популярные новости'"),
            ("ближайшие мероприятия", "Найден блок 'ближайшие мероприятия'"),
            ("написать нам", "Найдено 'написать нам'"),
            ("условия использования", "Найдено 'условия использования'"),
            ("пользовательское соглашение", "Найдено 'пользовательское соглашение'"),
        ]
        
        for pattern, warning in garbage_patterns:
            if pattern in content_lower:
                warnings.append(warning)
        
        # Проверяем наличие телефонов формата +7 или 8-800
        if re.search(r'[\+]?[78][\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}', content):
            warnings.append("Найдены телефоны")
        
        # Проверяем минимальную длину (слишком короткий контент = плохая очистка)
        if len(content) < 100:
            warnings.append(f"Контент слишком короткий ({len(content)} символов)")
        
        passed = len(warnings) == 0
        
        return {
            "passed": passed,
            "warnings": warnings
        }

    async def generate_article_from_external_content(
        self,
        external_content: str,
        source_url: str,
        source_domain: str,
        project: ProjectType,
        formatting_options=None
    ) -> Tuple[GeneratedArticle, Dict]:
        """
        Генерация медицинской статьи из внешнего контента (URL)

        Args:
            external_content: Контент статьи (markdown из Jina AI)
            source_url: URL источника
            source_domain: Домен источника
            project: Тип проекта для адаптации
            formatting_options: Опции форматирования (опционально)

        Returns:
            Tuple[GeneratedArticle, Dict]: Сгенерированная статья и метрики
        """
        start_time = time.time()

        # Определяем специализацию для проекта
        project_info = {
            ProjectType.GYNECOLOGY: {
                "specialization": "гинекологии и женского здоровья",
                "audience": "акушеров-гинекологов, репродуктологов",
                "focus": "репродуктивное здоровье, гормональные аспекты, онкогинекология"
            },
            ProjectType.THERAPY: {
                "specialization": "терапии и общей медицины",
                "audience": "терапевтов, врачей общей практики",
                "focus": "внутренние болезни, диагностика, коморбидность"
            },
            ProjectType.PEDIATRICS: {
                "specialization": "педиатрии и детского здоровья",
                "audience": "педиатров, неонатологов",
                "focus": "детское здоровье, возрастные особенности, вакцинация"
            }
        }

        info = project_info.get(project, project_info[ProjectType.THERAPY])

        # Читаем настройки длины статьи
        try:
            min_length_setting = settings_service.get_app_setting("article_min_length")
            min_length = int(min_length_setting.setting_value) if min_length_setting and min_length_setting.setting_value else 2500

            max_length_setting = settings_service.get_app_setting("article_max_length")
            max_length = int(max_length_setting.setting_value) if max_length_setting and max_length_setting.setting_value else 4000
        except Exception:
            min_length = 2500
            max_length = 4000

        system_prompt = f"""Ты — опытный медицинский журналист, специализирующийся на {info['specialization']}.
Твоя задача — адаптировать статью из внешнего источника для медицинского портала, ориентированного на {info['audience']}.

🎯 ГЛАВНАЯ ЗАДАЧА:
Создать УНИКАЛЬНУЮ, профессиональную медицинскую статью на основе внешнего материала.
Фокус: {info['focus']}

🔄 ПРИНЦИПЫ АДАПТАЦИИ:

1️⃣ **АНАЛИЗИРУЙ И АДАПТИРУЙ**:
- Извлеки ключевую медицинскую информацию из источника
- Дополни профессиональным медицинским контекстом
- Адаптируй под целевую аудиторию — {info['audience']}
- НЕ копируй текст, а переработай в уникальный материал

2️⃣ **СТРУКТУРА**:
- Создай органичную структуру под контент
- Используй профессиональные медицинские заголовки
- Логичное развитие темы от введения к выводам

3️⃣ **МЕДИЦИНСКАЯ ЭКСПЕРТИЗА**:
- Дополни медицинской терминологией и контекстом
- Укажи механизмы, патогенез, этиологию где уместно
- Добавь клиническую значимость для целевой специальности
- Используй профессиональные сокращения: МКБ-10, ЭКГ, МРТ и т.д.

4️⃣ **ФОРМАТИРОВАНИЕ**:
- Используй HTML теги: <p>, <h2>, <h3>, <strong>, <em>, <ul>, <li>, <blockquote>
- ОБЯЗАТЕЛЬНО: один <br> ДО и ПОСЛЕ каждого заголовка
- Выделяй ключевые термины и цифры через <strong>
- Названия исследований, журналов — через <em>

5️⃣ **SEO ОПТИМИЗАЦИЯ**:
- seo_title: до 60 символов, медицинский контекст
- seo_description: до 160 символов, ключевая суть
- seo_keywords: 5-7 релевантных медицинских терминов

6️⃣ **ИЗОБРАЖЕНИЕ**:
- Создай детальный промпт НА РУССКОМ для реалистичного медицинского изображения
- Промпт должен ТОЧНО отражать ОСНОВНУЮ ТЕМУ статьи
- Варианты в зависимости от темы:
  * Для статей о лекарствах/препаратах: "таблетки, капсулы, медикаменты на светлом фоне"
  * Для статей о питании/диете: "здоровая еда, фрукты, овощи, полезные продукты"
  * Для статей о симптомах/болезнях: "медицинская иллюстрация [орган/часть тела], анатомия"
  * Для статей о диагностике: "медицинское оборудование, современный аппарат для диагностики"
  * Для статей о профилактике: "здоровый образ жизни, физическая активность, wellness"
  * Для статей об исследованиях: "научная лаборатория, исследования, микроскоп"
- ВАЖНО: НЕ используй общие шаблоны! Промпт должен быть уникальным для каждой статьи
- ИЗБЕГАЙ: зданий клиник, врачей в масках, общих медицинских интерьеров

📏 ТРЕБОВАНИЯ К ОБЪЕМУ:
- Примерная длина: {min_length+500} символов ЧИСТОГО ТЕКСТА (без HTML)
- Диапазон: {min_length}-{max_length} символов
- Главное — качественное раскрытие темы!

⚠️ ВАЖНО:
- Создавай УНИКАЛЬНЫЙ контент, а не копируй источник
- Адаптируй под профессиональную медицинскую аудиторию
- Дополняй медицинским контекстом и экспертизой
- Указывай источник: "По данным {source_domain}..."

Верни результат СТРОГО в JSON, без комментариев:
{{
  "news_text": "Профессиональная HTML-статья примерно {min_length+500} символов чистого текста",
  "seo_title": "SEO заголовок до 60 символов",
  "seo_description": "SEO описание до 160 символов",
  "seo_keywords": ["ключевое_слово_1", "ключевое_слово_2", "ключевое_слово_3"],
  "image_prompt": "КРАСИВОЕ и ПРИВЛЕКАТЕЛЬНОЕ описание на русском языке (например: 'стеклянная банка с витаминами на мраморном столе у окна, утреннее солнце' ИЛИ 'тарелка с яркими свежими овощами, вид сверху, естественное освещение' ИЛИ 'руки держат чашку чая на уютном фоне'). ИЗБЕГАЙ: органов, крови, шприцев, больниц",
  "image_url": "https://example.com/image.jpg"
}}"""

        user_prompt = f"""ИСТОЧНИК: {source_url} ({source_domain})

КОНТЕНТ ДЛЯ АДАПТАЦИИ:
{external_content[:8000]}

🎯 ЗАДАЧА:
Создай профессиональную медицинскую статью для проекта {project.value}, адаптировав этот материал для {info['audience']}.

⚠️ ВАЖНО:
1. Создай УНИКАЛЬНЫЙ контент — не копируй, а переработай
2. Дополни медицинским контекстом и профессиональной экспертизой
3. Адаптируй под фокус: {info['focus']}
4. Добавь <br> ДО и ПОСЛЕ каждого заголовка
5. Примерный объем: {min_length+500} символов чистого текста

💡 Упоминай источник где уместно: "По данным {source_domain}...", "Исследование, опубликованное на {source_domain}..." и т.д."""

        # Добавляем инструкции форматирования если заданы
        if formatting_options:
            formatting_instructions = self._build_formatting_instructions(formatting_options)
            system_prompt += f"\n\n🎛️ ДОПОЛНИТЕЛЬНЫЕ ТРЕБОВАНИЯ К ФОРМАТИРОВАНИЮ:\n{formatting_instructions}"

        try:
            # Читаем модель из настроек
            try:
                gen_model_setting = settings_service.get_app_setting("openai_generation_model")
                model_name = gen_model_setting.setting_value if gen_model_setting and gen_model_setting.setting_value else "gpt-4o"

                temperature_setting = settings_service.get_app_setting("openai_temperature")
                temperature_value = float(temperature_setting.setting_value) if temperature_setting and temperature_setting.setting_value else 0.6

                max_tokens_setting = settings_service.get_app_setting("openai_max_tokens")
                max_tokens_value = int(max_tokens_setting.setting_value) if max_tokens_setting and max_tokens_setting.setting_value else 8000
            except Exception:
                model_name = "gpt-4o"
                temperature_value = 0.6
                max_tokens_value = 8000

            # Модели-кандидаты с фолбэками
            preferred_order = [model_name, "gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo-16k"]
            seen = set()
            candidates = []
            for m in preferred_order:
                if m and m not in seen:
                    seen.add(m)
                    candidates.append(m)

            last_error = None
            used_model = model_name
            response = None
            for candidate in candidates:
                try:
                    response = await self.provider.get_completion(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        model=candidate,
                        temperature=temperature_value,
                        max_tokens=max_tokens_value,
                        frequency_penalty=0.3,
                        presence_penalty=0.3
                    )
                    used_model = candidate
                    break
                except Exception as e:
                    last_error = e
                    err_msg = str(e).lower()
                    if "model_not_found" in err_msg or "404" in err_msg:
                        continue
                    raise

            if response is None:
                raise last_error or Exception("No available model for URL article generation")

            # Парсим JSON ответ
            content = response["content"].strip()

            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()

            # Парсинг JSON с обработкой ошибок
            try:
                result_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Response content: {content}")

                # Попытка исправить JSON
                try:
                    fixed_content = re.sub(r'"\s*\n\s*"', '",\n  "', content)
                    fixed_content = re.sub(r'}\s*\n\s*"', '},\n  "', fixed_content)
                    fixed_content = re.sub(r']\s*\n\s*"', '],\n  "', fixed_content)

                    # Добавляем закрывающую скобку если отсутствует
                    fixed_content = fixed_content.strip()
                    if not fixed_content.endswith('}'):
                        fixed_content += '\n}'
                        logger.info("Added missing closing brace to JSON")

                    result_data = json.loads(fixed_content)
                    logger.info("Successfully fixed JSON in generate_article_from_external_content")
                except json.JSONDecodeError:
                    raise Exception(f"Ошибка парсинга ответа AI: {str(e)}")

            # Генерируем профессиональный промпт для изображения через GPT-4o-mini
            # Используем seo_title и seo_description из сгенерированной статьи
            logger.info("Generating image prompt via GPT-4o-mini...")
            image_prompt = await self.generate_image_prompt(
                result_data["seo_description"],
                result_data["seo_title"]
            )

            # Генерируем изображение по полученному промпту
            image_url = await self._generate_image(image_prompt)
            result_data["image_url"] = image_url
            result_data["image_prompt"] = image_prompt  # Сохраняем для отображения

            # Проверяем длину
            clean_text = re.sub(r'<[^>]*>', '', result_data["news_text"])
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            text_length = len(clean_text)

            # Создаем объект
            article = GeneratedArticle(
                news_text=result_data["news_text"],
                seo_title=result_data["seo_title"],
                seo_description=result_data["seo_description"],
                seo_keywords=result_data["seo_keywords"],
                image_prompt=result_data["image_prompt"],
                image_url=result_data["image_url"]
            )

            # Метрики
            processing_time = time.time() - start_time
            target_length = formatting_options.target_length if formatting_options else min_length
            metrics = {
                "model_used": used_model,
                "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                "processing_time_seconds": processing_time,
                "success": True,
                "text_length_clean": text_length,
                "text_length_html": len(result_data["news_text"]),
                "target_length": target_length,
                "source_url": source_url,
                "source_domain": source_domain
            }

            logger.info(f"Article generated from URL {source_url}: {text_length} clean characters. Tokens: {response.get('usage', {}).get('total_tokens', 0)}, Time: {processing_time:.2f}s")

            return article, metrics

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error in generate_article_from_external_content: {e}")

            metrics = {
                "model_used": model_name,
                "tokens_used": 0,
                "processing_time_seconds": processing_time,
                "success": False,
                "error": str(e)
            }

            raise Exception(f"Ошибка при генерации статьи из URL: {str(e)}")

    async def generate_full_article(self, summary: str, facts: List[str], project: ProjectType, original_title: str, formatting_options=None) -> Tuple[GeneratedArticle, Dict]:
        """
        Генерация подробной НОВОСТИ (2500-4000 символов) с SEO

        Args:
            summary: Выжимка новости (до 700 символов)
            facts: Список ключевых фактов
            project: Тип проекта (для SEO-оптимизации)
            original_title: Оригинальный заголовок

        Returns:
            Tuple[GeneratedArticle, Dict]: Сгенерированная новость (минимум 2500 символов) с динамическим image_prompt и метрики
        """
        start_time = time.time()
        
        # Определяем специализацию и аудиторию для проекта
        project_info = {
            ProjectType.GYNECOLOGY: {
                "specialization": "гинекологии и женского здоровья",
                "audience": "акушеров-гинекологов, репродуктологов и других медицинских специалистов",
                "keywords_base": ["гинекология", "женское здоровье", "репродуктивная система", "акушерство", "менструальный цикл", "овуляция", "беременность"],
                "professional_focus": "Акцент на гормональные механизмы, репродуктивные технологии, онкогинекологию, эндокринологические аспекты"
            },
            ProjectType.THERAPY: {
                "specialization": "терапии и общей медицины",
                "audience": "терапевтов, врачей общей практики и узких специалистов",
                "keywords_base": ["терапия", "лечение", "диагностика", "здоровье", "внутренние болезни", "коморбидность", "полипрагмазия"],
                "professional_focus": "Акцент на дифференциальную диагностику, коморбидные состояния, персонализированную медицину, доказательную медицину"
            },
            ProjectType.PEDIATRICS: {
                "specialization": "педиатрии и детского здоровья", 
                "audience": "педиатров, неонатологов, детских узких специалистов",
                "keywords_base": ["педиатрия", "детское здоровье", "развитие ребенка", "неонатология", "вакцинация", "педиатрическая фармакология"],
                "professional_focus": "Акцент на возрастные особенности, физиологию развития, педиатрические дозировки, семейно-центрированный подход"
            }
        }
        
        info = project_info.get(project, project_info[ProjectType.THERAPY])

        # Читаем настройки минимальной и максимальной длины статьи
        try:
            min_length_setting = settings_service.get_app_setting("article_min_length")
            min_length = int(min_length_setting.setting_value) if min_length_setting and min_length_setting.setting_value else 2500

            max_length_setting = settings_service.get_app_setting("article_max_length")
            max_length = int(max_length_setting.setting_value) if max_length_setting and max_length_setting.setting_value else 4000
        except Exception:
            min_length = 2500
            max_length = 4000

        system_prompt = f"""Ты — опытный медицинский журналист с 15-летним стажем в области {info['specialization']}.
Создай РАЗВЕРНУТУЮ профессиональную статью для медицинского портала, ориентированную на {info['audience']}.

🎯 СПЕЦИАЛИЗАЦИЯ: {info['professional_focus']}

🚨 КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ:

📏 ОБЪЕМ СТАТЬИ: Стремись к {min_length+500} символам ЧИСТОГО ТЕКСТА (без HTML тегов), допустимый диапазон {min_length}-{max_length} символов.
⚠️ ВАЖНО: Символы считаются БЕЗ HTML тегов - только чистый текст, который увидит читатель!
💡 Главное - качественное раскрытие темы, а не точное попадание в количество символов.

🎯 ПРИНЦИПЫ СОЗДАНИЯ УНИКАЛЬНОЙ МЕДИЦИНСКОЙ СТАТЬИ:

1️⃣ АНАЛИЗИРУЙ КОНТЕНТ И ВЫБИРАЙ ПОДХОДЯЩУЮ СТРУКТУРУ:

📚 **Для исследований**: Методология → Результаты → Значение → Применение
🏥 **Для клинических случаев**: Случай → Диагностика → Лечение → Исход → Выводы
📊 **Для эпидемиологии**: Статистика → Анализ → Факторы риска → Прогнозы
⚖️ **Для инцидентов**: Хронология → Расследование → Ответственные → Последствия
🔬 **Для препаратов**: Механизм → Испытания → Эффективность → Безопасность → Перспективы
🏛️ **Для политики**: Суть → Обоснование → Реакция → Влияние → Реализация

2️⃣ СОЗДАВАЙ ОРГАНИЧНУЮ СТРУКТУРУ ПОД КОНТЕНТ:

🔹 **Всегда начинай с сильного лидера** (100-150 слов) с ключевыми фактами

🔹 **Выбирай заголовки исходя из СОДЕРЖАНИЯ**, а не шаблона:

🏥 **Клинические статьи**: "Этиология и патогенез", "Клиническая картина и симптоматика", "Диагностический алгоритм", "Современные методы лечения", "Прогноз и профилактика", "Клинические рекомендации"

🔬 **Исследовательские**: "Дизайн и методология исследования", "Характеристика выборки", "Результаты и статистический анализ", "Обсуждение полученных данных", "Клиническая значимость", "Ограничения исследования"

📊 **Эпидемиологические**: "Эпидемиологическая ситуация", "Факторы риска и группы риска", "Динамика заболеваемости", "Региональные особенности", "Стратегии профилактики", "Экономические аспекты"

💊 **Фармакологические**: "Фармакокинетика и фармакодинамика", "Показания к применению", "Режим дозирования", "Побочные эффекты и противопоказания", "Лекарственные взаимодействия", "Клинический опыт применения"

⚖️ **Происшествия/Новости**: "Хронология событий", "Медицинские аспекты", "Реакция профессионального сообщества", "Анализ причин", "Выводы и рекомендации"

🎯 **ВАЖНО**: НЕ используй одинаковые заголовки! Пусть каждая статья имеет УНИКАЛЬНУЮ структуру, подходящую именно для этой новости!

3️⃣ ПРОФЕССИОНАЛЬНОЕ РЕДАКТОРСКОЕ ФОРМАТИРОВАНИЕ:

🎨 ПОЛНАЯ СВОБОДА РЕДАКТОРА - используй ВСЕ доступные HTML-элементы для создания читабельного, профессионального контента:

📝 **Базовые элементы структуры:**
• <p> — абзацы (варьируй длину под содержание)
• <h2>, <h3>, <h4> — заголовки разных уровней (ОБЯЗАТЕЛЬНО добавляй один пробел до и после заголовков!)
• <div> — блоки для группировки контента
• <br> — одинарные переносы для создания пустых строк между блоками

✨ **Акценты и выделения:**
• <strong> — важные термины, цифры, ключевые факты
• <em> — названия препаратов, исследований, журналов
• <u> — подчеркивания для особых случаев
• <mark> — выделение критически важной информации

📋 **Списки и структуры:**
• <ul><li> — маркированные списки
• <ol><li> — нумерованные списки
• <dl><dt><dd> — списки определений

📊 **Дополнительные элементы:**
• <blockquote> — важные цитаты и выделенные блоки (используй только если требуется)
• <br> — разрывы строк где это уместно
• <hr> — разделители между большими блоками
• <span> — локальные выделения в тексте

🎯 **ПРИНЦИП**: Действуй как ПРОФЕССИОНАЛЬНЫЙ РЕДАКТОР медицинского издания. Используй любые HTML-теги, которые улучшат восприятие и структуру статьи. НЕ ограничивайся базовым набором!

🏥 ПРОФЕССИОНАЛЬНАЯ МЕДИЦИНСКАЯ ЛЕКСИКА:
✅ Используй точную медицинскую терминологию (МКБ-10, анатомические названия, фармакологические термины)
✅ Указывай конкретные цифры, статистику, дозировки в <strong>
✅ Ссылайся на исследования, журналы, клинические рекомендации в <em>
✅ Структурируй информацию логично с медицинской точки зрения
✅ Избегай популярных упрощений - пиши для медицинских специалистов
✅ Используй профессиональные сокращения: ЭКГ, МРТ, КТ, УЗИ, ОАК, БАК и т.д.
✅ Указывай механизмы действия, патогенез, этиологию
✅ Приводи дифференциальную диагностику где уместно

⚠️ КАЧЕСТВЕННЫЕ КРИТЕРИИ ПРОФЕССИОНАЛЬНОЙ СТАТЬИ:
• Объем: в диапазоне {min_length}-{max_length} символов ЧИСТОГО ТЕКСТА (без HTML) ✓
• Структура: органичная, подходящая под конкретный контент ✓
• Форматирование: профессиональное, разнообразное ✓
• Медицинская терминология: точная и грамотная ✓
• Уникальность: каждая статья с индивидуальной структурой ✓
• Читабельность: логичная подача информации ✓
• Полнота раскрытия: все важные аспекты темы освещены ✓

📰 РЕДАКТОРСКАЯ СВОБОДА В СТРУКТУРИРОВАНИИ:

🎯 **ГЛАВНЫЙ ПРИНЦИП**: Ты - ПРОФЕССИОНАЛЬНЫЙ МЕДИЦИНСКИЙ РЕДАКТОР. Создавай статью так, как считаешь лучшим для конкретного контента.

🎨 **ТВОРЧЕСКАЯ СВОБОДА**:
• Определи сам, сколько нужно разделов (может быть 2, может 5)
• Создавай заголовки, которые точно отражают суть блока
• Используй любые элементы форматирования для удобства чтения
• Делай акценты там, где это важно для понимания
• Структурируй информацию логично, но НЕ по шаблону

🔍 **ОРИЕНТИРЫ ДЛЯ ВДОХНОВЕНИЯ** (не правила, а идеи):
• Можешь начать с контекста проблемы
• Можешь выделить ключевые факты в отдельный блок
• Можешь сделать акцент на практических последствиях
• Можешь завершить выводами или перспективами (если это органично!)

💡 **ОСНОВНОЕ**: Пиши как журналист высокого класса, которому нужно донести медицинскую информацию профессионально и точно!

🔬 **ТРЕБОВАНИЯ К НАУЧНОЙ СТРОГОСТИ:**
• Используй доказательную базу и ссылайся на уровни доказательности
• Указывай ограничения и противопоказания
• Приводи конкретные цифры, статистику, доверительные интервалы
• Упоминай методологию исследований где уместно
• Обозначай степень рекомендации (IA, IB, IIA, IIB, III)
• Указывай источники рекомендаций (ВОЗ, РКО, РОАГ, СПР и др.)

📐 **КРИТИЧЕСКИ ВАЖНО - ФОРМАТИРОВАНИЕ С ПРОБЕЛАМИ:**
• Каждый заголовок должен иметь ОДНУ пустую строку ПЕРЕД ним и ОДНУ пустую строку ПОСЛЕ него
• Используй ОДИНАРНЫЙ <br> для создания пустых строк между заголовком и текстом
• Пример правильного форматирования: "<p>Текст абзаца.</p><br><h2>Заголовок раздела</h2><br><p>Новый абзац после заголовка.</p>"
• НЕ используй двойные <br><br> - только одинарные <br>!
• ЭТО ОБЯЗАТЕЛЬНОЕ ТРЕБОВАНИЕ для читабельности статьи!

4️⃣ ТРЕБОВАНИЯ К SEO:
- `seo_title` — до 60 символов
- `seo_description` — до 160 символов  
- `seo_keywords` — 5–7 ключевых слов/фраз по теме

5️⃣ ТРЕБОВАНИЯ К ИЗОБРАЖЕНИЮ:
- `image_prompt` — МАКСИМАЛЬНО КОНКРЕТНОЕ описание НА РУССКОМ ЯЗЫКЕ для красивого фотореалистичного изображения
- КРИТИЧЕСКИ ВАЖНО: Создай ПРИВЛЕКАТЕЛЬНОЕ изображение, которое передает СУТЬ статьи, но НЕ шокирует
- ОБЯЗАТЕЛЬНЫЕ элементы промпта:
  1) Конкретный объект/концепция (что именно изображено)
  2) Визуальные детали (цвет, свет, композиция)
  3) Настроение и стиль (спокойное, позитивное, профессиональное)
  4) Техника съемки (студийное фото, естественное освещение, крупный план)

- Варианты в зависимости от ТЕМЫ статьи (ВЫБИРАЙ КРАСИВЫЕ И ПРИВЛЕКАТЕЛЬНЫЕ КОНЦЕПЦИИ):
  * Лекарства/препараты → "элегантная стеклянная баночка с витаминами на светлом деревянном столе у окна, утреннее солнце, минималистичный стиль"
  * Питание/диета → "красочная композиция из свежих фруктов и овощей на мраморной поверхности, вид сверху, естественные цвета, студийная съемка"
  * Здоровье/wellness → "руки держат чашку травяного чая на уютном текстильном фоне, мягкое освещение, концепция заботы о здоровье"
  * Активность/спорт → "человек в спортивной одежде на фоне природы на рассвете, вдохновляющая атмосфера, активный образ жизни"
  * Беременность/материнство → "беременная женщина в светлом платье у окна с естественным светом, нежная атмосфера, профессиональная фотосъемка"
  * Детское здоровье → "счастливый ребенок играет на свежем воздухе в парке, яркие естественные цвета, радостная атмосфера"
  * Ментальное здоровье → "спокойная сцена: открытая книга и чашка чая на подоконнике, утренний свет, концепция релаксации"
  * Сон/отдых → "уютная спальня в пастельных тонах с мягким постельным бельем, утренний свет через занавески, атмосфера покоя"
  * Профилактика → "свежие продукты и вода на кухонном столе, яркие цвета, концепция здорового образа жизни, естественное освещение"
  * Исследования/наука → "современный микроскоп на лабораторном столе с размытым фоном, профессиональное освещение, научная атмосфера"
  * Инновации/технологии → "современные технологии в медицине: планшет с медицинскими данными на светлом столе, минималистичный стиль"
  * Старение/долголетие → "руки пожилого человека держат цветок, естественное освещение, концепция мудрости и заботы"

- СТРОГИЕ ПРАВИЛА:
  ✅ ОБЯЗАТЕЛЬНО: Красивые, эстетичные, привлекательные изображения
  ✅ ОБЯЗАТЕЛЬНО: Мягкие, естественные цвета и освещение
  ✅ ОБЯЗАТЕЛЬНО: Позитивное настроение и профессиональная композиция
  ✅ ОБЯЗАТЕЛЬНО: Конкретные объекты, НО красиво оформленные
  ❌ СТРОГО ИЗБЕГАЙ: Органы, внутренности, кровь, медицинские процедуры
  ❌ СТРОГО ИЗБЕГАЙ: Больницы, клиники, медицинские кабинеты, белые халаты
  ❌ СТРОГО ИЗБЕГАЙ: Шприцы, иглы, медицинские инструменты (ЕСЛИ тема НЕ о вакцинации)
  ❌ СТРОГО ИЗБЕГАЙ: Анатомические модели, схемы органов, медицинские иллюстрации
  ❌ СТРОГО ИЗБЕГАЙ: Таблетки россыпью, блистеры с лекарствами (лучше: баночка витаминов)

- ПРИМЕРЫ ПРАВИЛЬНЫХ ПРОМПТОВ:
  ✅ "стеклянная банка с разноцветными витаминами на белом мраморном столе у окна, утреннее солнце, минималистичная композиция"
  ✅ "тарелка с радужным салатом из свежих овощей на деревянном столе, вид сверху, яркие естественные цвета"
  ✅ "женские руки держат чашку зеленого чая на фоне уютного пледа, мягкое освещение, концепция wellness"
  ✅ "молодая женщина медитирует на коврике в светлой комнате с растениями, утренний свет, спокойная атмосфера"
  ✅ "семья на прогулке в парке осенью, естественные цвета, радостная атмосфера, концепция здоровья"

- ПРИМЕРЫ НЕПРАВИЛЬНЫХ ПРОМПТОВ:
  ❌ "пробирки с кровью" (слишком медицинское, неприятное)
  ❌ "хирургические инструменты" (пугающее, не эстетичное)
  ❌ "анатомическая модель органов" (не привлекательное)
  ❌ "врач в белом халате" (слишком клиническое)
  ❌ "блистер с таблетками" (скучное, депрессивное)

🎯 ФИНАЛЬНАЯ ПРОВЕРКА ПЕРЕД ОТПРАВКОЙ:
1. Убедись, что все важные аспекты темы раскрыты
2. Проверь профессиональность медицинской терминологии
3. Статья должна быть содержательной и информативной
4. Примерный объем: {min_length+500} символов чистого текста (±200 символов)

Верни результат СТРОГО в JSON, без комментариев:
{{
  "news_text": "ПРОФЕССИОНАЛЬНАЯ HTML-статья примерно {min_length+500} символов чистого текста (±200 символов). Работай как ОПЫТНЫЙ РЕДАКТОР: создай уникальную структуру, используй разнообразное форматирование, делай акценты где нужно. Главное - качественное раскрытие темы!",
  "seo_title": "SEO заголовок до 60 символов",
  "seo_description": "SEO описание до 160 символов",
  "seo_keywords": ["ключевое_слово_1", "ключевое_слово_2", "ключевое_слово_3"],
  "image_prompt": "КРАСИВОЕ и ЭСТЕТИЧНОЕ описание на русском языке с визуальными деталями (цвет, свет, настроение). Примеры: 'стеклянная банка с витаминами на белом мраморе у окна, мягкий утренний свет, минимализм' ИЛИ 'тарелка с радужным салатом из свежих овощей, вид сверху, яркие естественные цвета' ИЛИ 'женские руки держат чашку зеленого чая на фоне уютного пледа, теплое освещение, wellness концепция'. СТРОГО ИЗБЕГАЙ: органов, крови, шприцев, медицинских инструментов, больниц, клиник",
  "image_url": "https://example.com/image.jpg"
}}"""

        facts_text = "\n".join([f"• {fact}" for fact in facts])
        
        user_prompt = f"""Оригинальный заголовок: {original_title}

Выжимка статьи:
{summary}

Ключевые факты:
{facts_text}

🎯 Создай ПРОФЕССИОНАЛЬНУЮ медицинскую статью на основе этих данных.
🎨 РАБОТАЙ КАК ОПЫТНЫЙ РЕДАКТОР: используй творческий подход к структуре и форматированию!
🚨 ВАЖНО: Применяй ЛЮБЫЕ HTML-теги для улучшения восприятия статьи!
📐 ОБЯЗАТЕЛЬНО: Добавляй ОДИНАРНЫЙ <br> ПЕРЕД и ПОСЛЕ каждого заголовка для читабельности!
📝 В JSON возвращай готовый HTML: используй <strong>, <em>, <u>, <mark>, <blockquote>, списки, разделители и др.

⚠️ ВАЖНО - КАЧЕСТВО И ПОЛНОТА:
1. Убедись, что все важные аспекты темы раскрыты
2. Проверь профессиональность медицинской терминологии  
3. Статья должна быть содержательной и полезной
4. Примерный объем: около {min_length+500} символов чистого текста (гибко)

🎯 ЦЕЛЬ: Создать уникальную, профессиональную статью с правильными пробелами между разделами и полным раскрытием темы!"""

        # Добавляем инструкции форматирования если заданы
        if formatting_options:
            formatting_instructions = self._build_formatting_instructions(formatting_options)
            system_prompt += f"\n\n🎛️ ДОПОЛНИТЕЛЬНЫЕ ТРЕБОВАНИЯ К ФОРМАТИРОВАНИЮ:\n{formatting_instructions}"

        # Читаем параметры генерации из настроек (если есть), с безопасными дефолтами
        try:
            gen_model_setting = settings_service.get_app_setting("openai_generation_model")
            model_name = (gen_model_setting.setting_value if gen_model_setting and gen_model_setting.setting_value else "gpt-4o")

            temperature_setting = settings_service.get_app_setting("openai_temperature")
            temperature_value = float(temperature_setting.setting_value) if temperature_setting and temperature_setting.setting_value else 0.6

            max_tokens_setting = settings_service.get_app_setting("openai_max_tokens")
            max_tokens_value = int(max_tokens_setting.setting_value) if max_tokens_setting and max_tokens_setting.setting_value else 8000

            # Модели-кандидаты с безопасными фолбэками
            preferred_order = [model_name, "gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo-16k"]
            seen = set()
            generation_model_candidates = []
            for m in preferred_order:
                if m and m not in seen:
                    seen.add(m)
                    generation_model_candidates.append(m)

            last_error = None
            used_generation_model = model_name
            response = None
            for candidate in generation_model_candidates:
                try:
                    response = await self.provider.get_completion(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        model=candidate,
                        temperature=temperature_value,
                        max_tokens=max_tokens_value,
                        frequency_penalty=0.2,
                        presence_penalty=0.2
                    )
                    used_generation_model = candidate
                    break
                except Exception as e:
                    last_error = e
                    err_msg = str(e).lower()
                    if "model_not_found" in err_msg or "404" in err_msg:
                        continue
                    raise
            if response is None:
                raise last_error or Exception("No available model for generation")
            
            # Извлекаем JSON из ответа
            content = response["content"].strip()
            
            # Пытаемся найти JSON в ответе
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            # Дополнительная очистка JSON: правильно обрабатываем переносы строк в значениях
            # Заменяем переносы строк только внутри строковых значений JSON, но НЕ в HTML контенте
            def fix_json_newlines(match):
                # Получаем содержимое строки (без кавычек)
                string_content = match.group(0)

                # Если это поле news_text с HTML, не заменяем переносы строк
                # чтобы сохранить HTML форматирование
                if '"news_text"' in string_content or any(html_tag in string_content for html_tag in ['<p>', '<br>', '<div>', '<h1>', '<h2>', '<h3>', '<strong>', '<em>']):
                    # Заменяем только системные символы, но сохраняем HTML структуру
                    return string_content.replace('\r', '\\r').replace('\t', '\\t')
                else:
                    # Для других полей заменяем все как обычно
                    return string_content.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

            # Исправляем переносы только в строковых значениях
            content = re.sub(r'"[^"]*"', fix_json_newlines, content, flags=re.DOTALL)
            
            # Попытка исправления типичных ошибок JSON
            try:
                result_data = json.loads(content)
            except json.JSONDecodeError as e:
                # Логируем ошибку для отладки
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Response content: {content}")
                
                # Попытка исправить отсутствующие запятые и закрывающие скобки
                try:
                    # Исправляем отсутствующие запятые между полями JSON
                    fixed_content = re.sub(r'"\s*\n\s*"', '",\n  "', content)
                    fixed_content = re.sub(r'}\s*\n\s*"', '},\n  "', fixed_content)
                    fixed_content = re.sub(r']\s*\n\s*"', '],\n  "', fixed_content)

                    # Проверяем, что JSON заканчивается на закрывающую скобку
                    fixed_content = fixed_content.strip()
                    if not fixed_content.endswith('}'):
                        # Добавляем закрывающую скобку, если она отсутствует
                        fixed_content += '\n}'
                        logger.info("Added missing closing brace to JSON")

                    result_data = json.loads(fixed_content)
                    logger.info("Successfully fixed JSON by adding missing commas/braces")
                except json.JSONDecodeError:
                    # Если исправление не помогло, выбрасываем исходную ошибку
                    raise Exception(f"Invalid JSON response from AI: {str(e)}")
            
            # Генерируем профессиональный промпт для изображения через GPT-4o-mini
            # На основе выжимки создаем уникальный английский промпт для Gemini
            logger.info("Generating image prompt via GPT-4o-mini...")
            image_prompt = await self.generate_image_prompt(summary, original_title)

            # Генерируем изображение по полученному промпту
            image_url = await self._generate_image(image_prompt)
            result_data["image_url"] = image_url
            result_data["image_prompt"] = image_prompt  # Сохраняем для отображения
            
            # Проверяем длину сгенерированной статьи
            # Подсчитываем длину чистого текста (без HTML тегов)
            clean_text = re.sub(r'<[^>]*>', '', result_data["news_text"])
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            text_length = len(clean_text)
            
            # Создаем объект GeneratedArticle
            article = GeneratedArticle(
                news_text=result_data["news_text"],
                seo_title=result_data["seo_title"],
                seo_description=result_data["seo_description"],
                seo_keywords=result_data["seo_keywords"],
                image_prompt=result_data["image_prompt"],
                image_url=result_data["image_url"]
            )
            
            # Метрики
            processing_time = time.time() - start_time
            target_length = formatting_options.target_length if formatting_options else min_length
            metrics = {
                "model_used": used_generation_model,
                "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                "processing_time_seconds": processing_time,
                "success": True,
                "text_length_clean": text_length,  # Длина чистого текста
                "text_length_html": len(result_data["news_text"]),  # Длина с HTML
                "target_length": target_length,
                "min_length": min_length,
                "max_length": max_length,
                "meets_length_requirements": min_length <= text_length <= max_length,
                "meets_target_length": abs(text_length - target_length) <= 300  # Допустимое отклонение ±300 символов
            }
            
            # Логируем результат с информацией о длине
            tokens_used = response.get("usage", {}).get("total_tokens", 0)
            target_length = formatting_options.target_length if formatting_options else min_length
            
            # Если статья слишком короткая (менее 70% от минимальной длины), попробуем сгенерировать еще раз
            if text_length < min_length * 0.7:
                logger.warning(f"Generated news is too short: {text_length} clean characters (minimum {min_length}, target {target_length}). Attempting regeneration...")
                
                # Попытка повторной генерации с более подробными инструкциями
                retry_prompt = f"""ВНИМАНИЕ! Предыдущая попытка дала слишком короткую статью ({text_length} символов).
Пожалуйста, создай более развернутую статью с большим количеством деталей.

{user_prompt}

💡 ДОПОЛНИТЕЛЬНО: Добавь больше деталей, примеров, контекста, научных данных для более полного раскрытия темы!
Примерный объем: около {target_length} символов чистого текста."""

                try:
                    retry_response = await self.provider.get_completion(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": retry_prompt}
                        ],
                        model=used_generation_model,
                        temperature=temperature_value * 0.8,  # Снижаем температуру для более предсказуемого результата
                        max_tokens=max_tokens_value,
                        frequency_penalty=0.3,
                        presence_penalty=0.3
                    )
                    
                    retry_content = retry_response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    retry_result_data = json.loads(retry_content)
                    
                    # Проверяем длину повторно сгенерированной статьи
                    retry_clean_text = re.sub(r'<[^>]*>', '', retry_result_data["news_text"])
                    retry_clean_text = re.sub(r'\s+', ' ', retry_clean_text).strip()
                    retry_text_length = len(retry_clean_text)
                    
                    if retry_text_length > text_length:
                        logger.info(f"Regeneration successful: {retry_text_length} clean characters (improved from {text_length})")
                        result_data = retry_result_data
                        text_length = retry_text_length
                        response = retry_response
                        
                except Exception as retry_error:
                    logger.error(f"Failed to regenerate article: {retry_error}")
                    # Используем оригинальную статью
            
            if text_length < min_length * 0.8:
                logger.warning(f"Generated news is short: {text_length} clean characters (target {target_length}). Tokens: {tokens_used}, Time: {processing_time:.2f}s")
            elif text_length > max_length * 1.2:
                logger.warning(f"Generated news is long: {text_length} clean characters (target {target_length}). Tokens: {tokens_used}, Time: {processing_time:.2f}s")
            else:
                logger.info(f"News generated successfully: {text_length} clean characters (target {target_length}, acceptable range). Tokens: {tokens_used}, Time: {processing_time:.2f}s")
            
            return article, metrics

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error in generate_full_article: {e}")
            
            metrics = {
                "model_used": locals().get("model_name", "gpt-4o-mini"),
                "tokens_used": 0,
                "processing_time_seconds": processing_time,
                "success": False,
                "error": str(e)
            }
            
            raise Exception(f"Ошибка при генерации статьи: {str(e)}")

    def _build_formatting_instructions(self, formatting_options) -> str:
        """Строит инструкции для форматирования на основе выбранных параметров"""
        instructions = []

        # Количество заголовков
        if formatting_options.headings_count == 0:
            instructions.append("📝 НЕ ИСПОЛЬЗУЙ заголовки (<h2>, <h3>) - только абзацы")
        elif formatting_options.headings_count <= 2:
            instructions.append(f"📝 Используй МАКСИМУМ {formatting_options.headings_count} заголовка")
        else:
            instructions.append(f"📝 Используй {formatting_options.headings_count} заголовков для структурирования")

        # Стиль написания
        if formatting_options.style.value == "structured":
            instructions.append("🏗️ СТРУКТУРИРОВАННЫЙ стиль: четко разделенные разделы с подзаголовками")
        elif formatting_options.style.value == "narrative":
            instructions.append("📖 ПОВЕСТВОВАТЕЛЬНЫЙ стиль: плавное изложение без четких разделов")
        elif formatting_options.style.value == "mixed":
            instructions.append("🎭 СМЕШАННЫЙ стиль: сочетание структурных элементов и повествования")

        # Длина абзацев
        if formatting_options.paragraph_length.value == "short":
            instructions.append(f"📏 КОРОТКИЕ абзацы: 1-2 предложения (примерно {formatting_options.sentences_per_paragraph} предложения)")
        elif formatting_options.paragraph_length.value == "medium":
            instructions.append(f"📏 СРЕДНИЕ абзацы: 3-4 предложения (примерно {formatting_options.sentences_per_paragraph} предложения)")
        elif formatting_options.paragraph_length.value == "long":
            instructions.append(f"📏 ДЛИННЫЕ абзацы: 5+ предложений (примерно {formatting_options.sentences_per_paragraph} предложения)")

        # Целевая длина
        instructions.append(f"📐 ПРИМЕРНАЯ ДЛИНА: около {formatting_options.target_length} символов ЧИСТОГО ТЕКСТА (±200 символов)")
        instructions.append(f"💡 Главное - качественное раскрытие темы, длина может варьироваться")

        # Списки и цитаты
        if formatting_options.use_lists:
            instructions.append("📋 ИСПОЛЬЗУЙ списки (<ul>, <ol>) для структурирования информации")
        else:
            instructions.append("🚫 НЕ используй списки - только абзацы")

        if formatting_options.use_quotes:
            instructions.append("💬 ИСПОЛЬЗУЙ цитаты экспертов в <blockquote> или выделяй в <em>")
        else:
            instructions.append("🚫 НЕ используй отдельные цитаты - интегрируй мнения в текст")

        return "\n".join(instructions)

    async def generate_image_prompt(self, summary: str, article_title: str) -> str:
        """
        Генерация профессионального промпта для изображения на основе выжимки статьи
        Использует GPT-4o-mini для создания детального английского промпта для Gemini

        Args:
            summary: Текст выжимки статьи
            article_title: Заголовок статьи

        Returns:
            Профессиональный промпт на английском языке для генерации изображения
        """
        system_prompt = """You are a professional medical image prompt engineer for AI image generation (Gemini 2.5 Flash).

Your task is to create detailed, professional English prompts for generating realistic medical/healthcare images based on article summaries.

CRITICAL REQUIREMENTS:
✅ Write ONLY in English (never Russian or other languages)
✅ Focus on photorealistic, documentary-style medical imagery
✅ Use professional medical terminology
✅ Describe lighting, composition, and atmosphere
✅ Specify "professional medical photography" style
✅ Keep prompts concise but descriptive (2-4 sentences)
✅ Avoid: cartoon, illustration, 3D render, abstract, fantasy, sci-fi

GOOD PROMPT STRUCTURE:
1. Main subject (doctor, patient, medical equipment, procedure)
2. Setting (hospital, clinic, lab, modern medical facility)
3. Lighting and mood (natural light, professional lighting, clean, bright)
4. Technical details (close-up, wide shot, documentary style)
5. Quality markers (photorealistic, high detail, professional medical photography)

EXAMPLE INPUT: "Статья о новом методе лечения диабета с помощью инсулиновой помпы"
EXAMPLE OUTPUT: "Professional medical photography of a modern insulin pump attached to a patient's body in a bright hospital room. Close-up shot showing the device details, natural lighting from window, clean white medical environment. Photorealistic, documentary style, suitable for medical education website, 16:9 aspect ratio."

Remember: The image should illustrate the article's medical topic professionally and realistically."""

        user_prompt = f"""Create a professional English prompt for generating a medical image based on this article:

TITLE: {article_title}

SUMMARY: {summary}

Generate a detailed English prompt (2-4 sentences) for creating a photorealistic medical image that captures the essence of this article. The image should be suitable for a professional medical education website."""

        try:
            response = await self.provider.get_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=200
            )

            image_prompt = response["content"].strip()

            # Убираем кавычки если есть
            image_prompt = image_prompt.strip('"').strip("'")

            logger.info(f"Generated image prompt: {image_prompt[:100]}...")
            return image_prompt

        except Exception as e:
            logger.error(f"Error generating image prompt: {e}")
            # Fallback промпт на английском
            fallback = f"Professional medical photography related to {article_title}. Clean hospital setting, natural lighting, photorealistic, documentary style, 16:9 aspect ratio."
            logger.warning(f"Using fallback image prompt: {fallback}")
            return fallback

    async def _generate_image(self, prompt: str) -> str:
        """
        Генерация изображения через KIE AI (Nano Banana - Google Gemini 2.5 Flash)

        Args:
            prompt: Промпт для генерации изображения

        Returns:
            str: URL сгенерированного изображения
        """
        try:
            import aiohttp
            service_url = settings.IMAGE_SERVICE_URL.rstrip("/") + "/api/images/generate"
            async with aiohttp.ClientSession() as session:
                async with session.post(service_url, json={"prompt": prompt}) as resp:
                    if resp.status != 200:
                        detail = await resp.text()
                        raise RuntimeError(f"Image service error {resp.status}: {detail}")
                    data = await resp.json()
                    image_url = data.get("image_url")
                    if not image_url:
                        raise RuntimeError("Image service returned no image_url")
                    logger.info(f"Image generated successfully via KIE AI service: {image_url}")
                    return image_url
        except Exception as e:
            logger.error(f"Error generating image via service: {e}")
            return "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?ixlib=rb-4.0.3&auto=format&fit=crop&w=1024&h=1024&q=80"

    async def regenerate_image(self, prompt: str) -> Tuple[str, Dict]:
        """
        Перегенерация изображения с новым промптом
        
        Args:
            prompt: Новый промпт для генерации
            
        Returns:
            Tuple[str, Dict]: URL изображения и метрики
        """
        start_time = time.time()
        
        try:
            image_url = await self._generate_image(prompt)
            
            processing_time = time.time() - start_time
            metrics = {
                "model_used": "kie-nano-banana",
                "tokens_used": 0,
                "processing_time_seconds": processing_time,
                "success": True
            }
            
            return image_url, metrics
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error in regenerate_image: {e}")

            metrics = {
                "model_used": "kie-nano-banana",
                "tokens_used": 0,
                "processing_time_seconds": processing_time,
                "success": False,
                "error": str(e)
            }
            
            raise Exception(f"Ошибка при перегенерации изображения: {str(e)}")


# Глобальный экземпляр сервиса
ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Получение экземпляра AI сервиса"""
    global ai_service
    if ai_service is None:
        if not settings.OPENAI_API_KEY:
            raise Exception("OPENAI_API_KEY не установлен в переменных окружения")
        ai_service = AIService(settings.OPENAI_API_KEY)
    return ai_service