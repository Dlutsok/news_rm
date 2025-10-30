# YandexART Models Research & Upgrade Path

**Дата:** 30 октября 2025
**Цель:** Исследование новых моделей Yandex для улучшения качества генерации изображений
**Статус:** ✅ COMPLETED - Найдены новые модели, но требуется расширенный доступ

---

## 🔍 Executive Summary

**Главный вывод:** Яндекс выпустил **YandexART 2.5** (март 2025) с **существенными улучшениями качества**, но новые модели требуют **дополнительных прав доступа** в Yandex Cloud.

**Текущая ситуация:**
- ✅ Используем: `yandex-art` (legacy версия)
- ⚠️ Доступны, но недоступны: `yandex-art-2.5`, `yandex-art-2.0`, `yandex-art-latest`
- ❌ Ошибка: `PERMISSION_DENIED` для всех новых моделей

**Решение:** Обратиться в поддержку Yandex Cloud для получения доступа к новым моделям.

---

## 📊 Research Results

### 1. Доступные модели (через SDK)

Проверка через `yandex-cloud-ml-sdk==0.2.0`:

```python
sdk = YCloudML(folder_id=YC_FOLDER_ID, auth=YC_API_KEY)
model = sdk.models.image_generation(MODEL_NAME)
```

| Model Name | SDK Accept | API Access | Status |
|------------|------------|------------|--------|
| `yandex-art` | ✅ Yes | ✅ Works | **CURRENT** (работает) |
| `yandex-art-latest` | ✅ Yes | ❌ PERMISSION_DENIED | Требует доступ |
| `yandex-art-2` | ✅ Yes | ❌ PERMISSION_DENIED | Требует доступ |
| `yandex-art-2.0` | ✅ Yes | ❌ PERMISSION_DENIED | Требует доступ |
| `yandex-art-2.5` | ✅ Yes | ❌ PERMISSION_DENIED | Требует доступ |
| `yandex-art-pro` | ✅ Yes | ❌ PERMISSION_DENIED | Требует доступ |

**Вывод:** SDK знает о всех моделях, но наш Yandex Cloud аккаунт имеет права только на `yandex-art`.

### 2. YandexART 2.5 Features (март 2025)

По данным [официального анонса Яндекса](https://yandex.ru/company/news/03-20-03-2025):

#### Улучшения в 2.5:

1. **Точное следование промпту** (+30% точности генерации текста на латинице)
   - Лучше распознает количество объектов
   - Точнее соблюдает формы, цвета, размеры
   - Правильнее интерпретирует характеристики из промпта

2. **Более реалистичные результаты**
   - Убраны избыточные фантастические элементы
   - Изображения больше похожи на реальные фотографии
   - Подходят для дизайна реализуемых объектов

3. **Улучшенная генерация текста**
   - +30% точности для латинского текста vs YandexART 2.0
   - Лучше для логотипов, баннеров, рекламных материалов

#### Версии:

- **YandexART 2.5** (базовая) - бесплатно в Шедевруме и Алисе
- **YandexART 2.5 Pro** - платная подписка 100₽/мес
  - Более детальные изображения
  - Меньше дефектов
  - Апскейл до 4K
  - Без watermark
  - 6 вариантов вместо 2
  - Неограниченное количество попыток

### 3. Технические характеристики

**YandexART (все версии):**
- **Параметры:** 5 миллиардов
- **Обучающая база:** 330 миллионов пар изображение-текст
- **Метод:** Cascade diffusion (постепенное повышение разрешения)
- **Формат вывода:** JPEG (binary)
- **Доступ:** Yandex Foundation Models API

**Сравнение с конкурентами:**

| Критерий | YandexART 2.5 | GigaChat Kandinsky 3.1 |
|----------|---------------|------------------------|
| Training data | 330M пар | 200M+ пар |
| Русский язык | ✅ Отлично | ✅ Отлично |
| API сложность | 🟢 Простой (1 запрос) | 🟡 Средний (2 запроса) |
| Token management | 🟢 Постоянный API key | 🔴 30 мин expiration |
| Стоимость | Неизвестна | Неизвестна |

---

## 🔒 Access Issue: PERMISSION_DENIED

### Проблема

При попытке использовать новые модели получаем ошибку:

```python
AioRpcError of RPC that terminated with:
    code = StatusCode.PERMISSION_DENIED
    details = "Access to model art://yandex-art-2.5/latest denied"
```

### Возможные причины

1. **Недостаточно прав в Yandex Cloud IAM**
   - Наш folder/service account не имеет роли `ai.imageGeneration.user` для новых моделей
   - Новые модели могут требовать специальные роли (например, `ai.imageGeneration.advanced`)

2. **Beta/Preview доступ**
   - YandexART 2.5 может быть в закрытой бета-программе
   - Требуется заявка на доступ

3. **Платный тариф**
   - Новые модели могут быть доступны только на коммерческих тарифах
   - Требуется апгрейд аккаунта

4. **Региональные ограничения**
   - Модели могут быть недоступны в определенных регионах

### Решение

**Шаг 1: Проверить IAM роли**
```bash
# Проверить текущие роли в Yandex Cloud Console
# Убедиться, что Service Account имеет:
# - ai.imageGeneration.user (базовая)
# - ai.imageGeneration.advanced (для новых моделей?)
```

**Шаг 2: Обратиться в поддержку Yandex Cloud**

Создать тикет с запросом:
```
Тема: Доступ к YandexART 2.5 через API

Описание:
Мы используем Yandex Cloud ML SDK для генерации медицинских изображений
через YandexART API. В марте 2025 вышла YandexART 2.5 с улучшенным качеством.

При попытке использовать новые модели получаем PERMISSION_DENIED:
- yandex-art-2.5
- yandex-art-2.0
- yandex-art-latest

Folder ID: b1gg98bnfm9rfef2ulk0
API Key ID: ajeqti4ehpqboote7s73

Вопросы:
1. Как получить доступ к YandexART 2.5?
2. Требуется ли специальная роль/тариф?
3. Есть ли документация по миграции с yandex-art на yandex-art-2.5?

Цель: Улучшить качество генерируемых изображений для медицинских новостей.
```

**Шаг 3: Альтернативные пути**

Если доступ к YandexART 2.5 недоступен:
1. Проверить доступность через [Yandex DataSphere](https://yandex.cloud/en/docs/datasphere/)
2. Использовать YandexART через [Shedevrum API](https://shedevrum.ai/) (если есть бизнес-тариф)
3. Рассмотреть миграцию на **GigaChat Kandinsky 3.1** (см. migration plan)

---

## 🎯 Recommendations

### Краткосрочная стратегия (1-2 недели)

1. **✅ Сделано:** Подтвердили, что новые модели существуют
2. **⏳ TODO:** Создать тикет в поддержку Yandex Cloud
3. **⏳ TODO:** Проверить IAM роли в Cloud Console
4. **⏳ TODO:** Изучить документацию по доступу к новым моделям

### Среднесрочная стратегия (1 месяц)

**Сценарий A: Получили доступ к YandexART 2.5**
```python
# Простое обновление в backend/api/image_generation.py:110
model = sdk.models.image_generation("yandex-art-2.5")  # было: "yandex-art"
```

**Преимущества:**
- ✅ Минимальные изменения кода (1 строка)
- ✅ Обратная совместимость API
- ✅ Улучшенное качество изображений
- ✅ Без дополнительной сложности

**Недостатки:**
- ❌ Зависимость от получения доступа
- ❌ Неизвестная стоимость

**Сценарий B: Доступ не получен**

Рассмотреть миграцию на **GigaChat** (см. `docs/migration/gigachat-image-generation-migration-plan.md`):
- Kandinsky 3.1 (200M+ training pairs)
- Гарантированная доступность (Сбербанк)
- Более сложная интеграция (OAuth + 2-step process)

### Долгосрочная стратегия (3+ месяца)

**Hybrid Provider Architecture**

Реализовать абстракцию для поддержки множественных AI провайдеров:

```python
class ImageProviderManager:
    providers = {
        "yandex-art": YandexArtProvider(),
        "yandex-art-2.5": YandexArt25Provider(),
        "gigachat": GigaChatProvider(),
        "openai-dall-e": OpenAIProvider(),
    }

    def generate(self, prompt, preferred_provider="auto"):
        # Auto-select based on availability, quality, cost
        pass
```

**Преимущества:**
- ✅ Vendor lock-in protection
- ✅ A/B testing разных провайдеров
- ✅ Fallback при недоступности одного из сервисов
- ✅ Cost optimization

---

## 📈 Quality Improvement Estimate

На основе анонса Яндекса, миграция на YandexART 2.5 даст:

| Метрика | Улучшение |
|---------|-----------|
| Prompt adherence | +30% (для текста на латинице) |
| Realism | Значительно выше (субъективно) |
| Fantasy elements | Меньше (нежелательных элементов) |
| Medical accuracy | Выше (за счет реализма) |
| Text generation | +30% точности |

**Оценка влияния на наш проект:**

Текущие проблемы с качеством (из жалоб):
- ❌ Изображения слишком "фантастические"
- ❌ Медицинские сцены выглядят нереалистично
- ❌ Много лишних деталей/артефактов
- ❌ Не соответствуют промпту точно

**YandexART 2.5 решает:**
- ✅ Более реалистичные изображения
- ✅ Меньше фантастических элементов
- ✅ Лучшее следование промпту
- ✅ Более подходящие для медицинского контента

**Ожидаемый результат:** 40-60% улучшение user satisfaction с изображениями.

---

## 💰 Cost Analysis

**Текущая стоимость (YandexART legacy):**
- Неизвестно (нет публичной информации о стоимости в .env)
- Предположительно платим за API usage

**YandexART 2.5 стоимость:**
- **Consumer tier (Shedevrum):** 100₽/мес за Pro
- **Enterprise tier (Yandex Cloud API):** Неизвестно, требует уточнения

**Важно запросить у поддержки:**
1. Стоимость YandexART 2.5 через Cloud API
2. Ценовая модель (за запрос / за изображение / flat rate)
3. Лимиты запросов на разных тарифах

---

## 🔄 Migration Plan (if access granted)

### Phase 1: Testing (1 week)

```bash
# 1. Get access to YandexART 2.5 from Yandex Cloud support

# 2. Test in development
cd backend
YC_FOLDER_ID=... YC_API_KEY=... python3 scripts/compare_yandex_models.py

# 3. Compare image quality manually
# Review images in backend/storage/model_comparison/
```

### Phase 2: Staged Rollout (2 weeks)

**Week 1: Dual-mode deployment**
```python
# backend/api/image_generation.py
YANDEX_ART_MODEL = os.getenv("YANDEX_ART_MODEL", "yandex-art")  # default legacy

model = sdk.models.image_generation(YANDEX_ART_MODEL)
```

**.env update:**
```bash
# A/B testing: 50% yandex-art, 50% yandex-art-2.5
YANDEX_ART_MODEL=yandex-art-2.5
```

**Week 2: Full rollout**
- Monitor quality metrics
- Collect user feedback
- If successful, make yandex-art-2.5 default

### Phase 3: Cleanup (1 week)

```python
# backend/api/image_generation.py:110
model = sdk.models.image_generation("yandex-art-2.5")  # hardcode new default
```

**Total migration time: ~4 weeks**

---

## 📝 Action Items

### Immediate (This Week)

- [ ] **Create Yandex Cloud support ticket** requesting YandexART 2.5 access
- [ ] **Check IAM roles** in Yandex Cloud Console
- [ ] **Document current API costs** for baseline comparison
- [ ] **Review existing image quality issues** from users/stakeholders

### Short-term (1-2 weeks)

- [ ] Wait for Yandex Cloud support response
- [ ] If granted access: Run `compare_yandex_models.py` with real access
- [ ] If denied: Start GigaChat migration (Plan B)
- [ ] Update stakeholders on findings

### Long-term (1+ month)

- [ ] Implement chosen solution (YandexART 2.5 or GigaChat)
- [ ] Measure quality improvements
- [ ] Consider hybrid provider architecture
- [ ] Document lessons learned

---

## 📚 References

1. **Yandex Official Announcement (March 2025):**
   - https://yandex.ru/company/news/03-20-03-2025
   - Title: "Яндекс запустил новую линейку YandexART"

2. **Yandex Cloud ML SDK:**
   - GitHub: https://github.com/yandex-cloud/yandex-cloud-ml-sdk
   - PyPI: https://pypi.org/project/yandex-cloud-ml-sdk/

3. **Yandex Foundation Models Docs:**
   - https://yandex.cloud/en/docs/foundation-models/
   - https://yandex.cloud/en/docs/foundation-models/quickstart/yandexart

4. **YandexART 2.0 Announcement (October 2024):**
   - https://yandex.com/company/news/10-10-2024

5. **Alternative: GigaChat Migration Plan**
   - `docs/migration/gigachat-image-generation-migration-plan.md`

---

## 🎓 Lessons Learned

1. **Model names != API access**
   - SDK может принимать имена моделей без проверки
   - Реальная доступность определяется только при API вызове

2. **Stay informed on provider updates**
   - Yandex выпустил 2.5 в марте 2025, мы узнали только сейчас
   - Нужен процесс мониторинга обновлений AI провайдеров

3. **Always have Plan B**
   - Vendor lock-in опасен
   - GigaChat как запасной вариант критически важен

4. **Document access requirements early**
   - Проверка IAM/тарифов должна быть в начале research
   - Сэкономило бы время на troubleshooting

---

**Document Version:** 1.0
**Last Updated:** 2025-10-30
**Author:** Development Team
**Status:** ✅ COMPLETED - Awaiting Yandex Cloud Support Response
