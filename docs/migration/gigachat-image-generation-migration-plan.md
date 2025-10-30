# GigaChat Image Generation Migration Plan

**Дата:** 30 октября 2025
**Цель:** Миграция с Yandex Cloud ML (YandexART) на GigaChat AI (Kandinsky 3.1) для генерации изображений
**Статус:** DRAFT - В разработке

---

## 1. Анализ текущей системы

### 1.1 Текущая архитектура (Yandex Cloud ML)

**Расположение кода:**
- `backend/api/image_generation.py` - основной API endpoint для генерации
- `backend/services/ai_service.py:1665` - интеграция в AI сервис
- `backend/api/news_generation.py:366,418` - использование в генерации новостей

**Технический стек:**
```python
# Текущая зависимость
yandex-cloud-ml-sdk==0.2.0

# Инициализация
from yandex_cloud_ml_sdk import YCloudML
sdk = YCloudML(folder_id=YC_FOLDER_ID, auth=YC_API_KEY)
model = sdk.models.image_generation("yandex-art")
```

**Переменные окружения:**
- `YC_FOLDER_ID` - Yandex Cloud Folder ID
- `YC_API_KEY` - Yandex Cloud API ключ
- `IMAGE_SERVICE_PUBLIC_BASE_URL` - базовый URL для доступа к изображениям

**Текущий workflow:**
1. Получение запроса с промптом через POST `/api/image-generation/generate`
2. Санитизация промпта (`sanitize_prompt()`) - удаление стилистических терминов
3. Обогащение промпта фотореалистичными инструкциями
4. Генерация через Yandex Cloud ML SDK
5. Сохранение в `backend/storage/images/` с UUID именем
6. Возврат публичного URL

**Параметры генерации:**
- `prompt` (str) - текстовый промпт
- `width_ratio` (1-2) - соотношение ширины
- `height_ratio` (1-2) - соотношение высоты
- `seed` (optional int) - для детерминированности

**Формат ответа:**
```json
{
  "image_url": "https://admin.news.rmevent.ru/images/{uuid}.jpeg",
  "model_used": "yandex-art",
  "success": true,
  "message": "Изображение успешно сгенерировано"
}
```

**Storage:**
- Путь: `backend/storage/images/`
- Формат: JPEG
- Naming: `{uuid}.jpeg`
- Размер: не ограничен
- Публикация: через nginx static файлы

---

## 2. GigaChat API Architecture

### 2.1 Основные отличия от Yandex Cloud ML

| Критерий | Yandex Cloud ML | GigaChat API |
|----------|-----------------|--------------|
| **Модель** | YandexART | Kandinsky 3.1 |
| **API тип** | Dedicated SDK | REST API через chat completions |
| **Аутентификация** | API Key + Folder ID | OAuth 2.0 (Access Token) |
| **Метод генерации** | Прямой вызов `image_generation()` | Chat completion с `function_call: auto` |
| **Формат ответа** | Прямые байты изображения | File ID → скачивание через отдельный endpoint |
| **Token lifetime** | Постоянный | 30 минут (требует обновления) |
| **Training data** | Неизвестно | 200+ миллионов image-text пар |
| **Стилизация** | Через промпт | System prompts + функции |
| **Поддержка** | РФ сервис | РФ сервис (Сбербанк) |

### 2.2 GigaChat API Workflow

**Этап 1: Получение Access Token**
```bash
POST https://ngw.devices.sberbank.ru:9443/api/v2/oauth
Headers:
  - Content-Type: application/x-www-form-urlencoded
  - Authorization: Basic <Authorization key>
  - RqUID: <unique-request-id>
Body:
  scope=GIGACHAT_API_PERS
```

**Ответ:**
```json
{
  "access_token": "eyJ...",
  "expires_at": 1730000000
}
```

**Этап 2: Генерация изображения**
```bash
POST https://gigachat.devices.sberbank.ru/api/v1/chat/completions
Headers:
  - Content-Type: application/json
  - Authorization: Bearer <access_token>
Body:
{
  "model": "GigaChat-2",  # или GigaChat-2-Pro/Max
  "messages": [
    {
      "role": "system",
      "content": "Ты - художник, создающий фотореалистичные изображения для медицинских новостей"
    },
    {
      "role": "user",
      "content": "Нарисуй {prompt}"
    }
  ],
  "function_call": "auto"
}
```

**Ответ:**
```json
{
  "choices": [
    {
      "message": {
        "content": "<img src=\"{file_id}\" fuse=\"true\"/>",
        "function_call": {
          "name": "text2image",
          "arguments": "{\"prompt\": \"...\"}"
        }
      }
    }
  ]
}
```

**Этап 3: Скачивание изображения**
```bash
POST https://gigachat.devices.sberbank.ru/api/v1/files/{file_id}/content
Headers:
  - Authorization: Bearer <access_token>
```

**Ответ:** Binary JPEG data

### 2.3 Ключевые особенности GigaChat

**Преимущества:**
- ✅ Более богатая обучающая база (200M+ пар)
- ✅ Поддержка стилизации через system prompts
- ✅ Интеграция с LLM для улучшения промптов
- ✅ Поддержка русского языка "из коробки"
- ✅ Доступность для бизнеса (Сбербанк)

**Недостатки:**
- ❌ Более сложный API (двухэтапный процесс)
- ❌ Token expiration каждые 30 минут
- ❌ Отсутствие прямого контроля над размерами изображения
- ❌ Дополнительный overhead (chat completion + file download)

---

## 3. Архитектура новой системы

### 3.1 Компонентная структура

```
backend/
├── services/
│   ├── gigachat_service.py          # NEW: GigaChat API client
│   ├── gigachat_auth_manager.py     # NEW: Token management
│   └── ai_image_provider.py         # NEW: Unified image provider interface
├── api/
│   └── image_generation.py          # MODIFIED: Support both providers
└── core/
    └── config.py                     # MODIFIED: Add GigaChat credentials
```

### 3.2 Unified Image Provider Interface

**Цель:** Абстракция для поддержки множественных AI провайдеров

```python
# backend/services/ai_image_provider.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class ImageGenerationRequest:
    prompt: str
    width_ratio: Optional[int] = 1
    height_ratio: Optional[int] = 1
    seed: Optional[int] = None
    style_instructions: Optional[str] = None

@dataclass
class ImageGenerationResult:
    image_bytes: bytes
    model_used: str
    metadata: Dict[str, Any]

class AIImageProvider(ABC):
    @abstractmethod
    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

class YandexCloudImageProvider(AIImageProvider):
    """Legacy Yandex Cloud ML provider"""
    # Existing implementation

class GigaChatImageProvider(AIImageProvider):
    """New GigaChat (Kandinsky 3.1) provider"""
    # New implementation
```

### 3.3 GigaChat Token Manager

**Проблема:** Access token живет только 30 минут
**Решение:** Автоматический refresh с кэшированием

```python
# backend/services/gigachat_auth_manager.py
import asyncio
from datetime import datetime, timedelta
from typing import Optional
import httpx

class GigaChatAuthManager:
    def __init__(self, client_id: str, auth_key: str, scope: str = "GIGACHAT_API_PERS"):
        self.client_id = client_id
        self.auth_key = auth_key
        self.scope = scope
        self._access_token: Optional[str] = None
        self._expires_at: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def get_access_token(self) -> str:
        """Get valid access token (auto-refresh if expired)"""
        async with self._lock:
            if self._is_token_valid():
                return self._access_token

            await self._refresh_token()
            return self._access_token

    def _is_token_valid(self) -> bool:
        if not self._access_token or not self._expires_at:
            return False
        # Refresh 5 minutes before expiration
        return datetime.now() < (self._expires_at - timedelta(minutes=5))

    async def _refresh_token(self):
        """Request new access token from GigaChat OAuth"""
        # Implementation details
        pass
```

### 3.4 GigaChat Service Implementation

```python
# backend/services/gigachat_service.py
import httpx
import logging
from typing import Optional, Dict, Any
from .gigachat_auth_manager import GigaChatAuthManager
from .ai_image_provider import AIImageProvider, ImageGenerationRequest, ImageGenerationResult

logger = logging.getLogger(__name__)

class GigaChatService(AIImageProvider):
    BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"

    def __init__(self, auth_manager: GigaChatAuthManager, model: str = "GigaChat-2"):
        self.auth_manager = auth_manager
        self.model = model
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """
        Generate image using GigaChat Kandinsky 3.1

        Steps:
        1. Get valid access token
        2. Send chat completion request with function_call: auto
        3. Extract file_id from response
        4. Download image bytes
        """
        try:
            # Step 1: Get token
            access_token = await self.auth_manager.get_access_token()

            # Step 2: Chat completion for image generation
            system_prompt = self._build_system_prompt(request)
            user_prompt = f"Нарисуй {request.prompt}"

            chat_response = await self._chat_completion(
                access_token=access_token,
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            # Step 3: Extract file_id
            file_id = self._extract_file_id(chat_response)

            # Step 4: Download image
            image_bytes = await self._download_image(access_token, file_id)

            return ImageGenerationResult(
                image_bytes=image_bytes,
                model_used=f"gigachat-kandinsky-3.1-{self.model}",
                metadata={
                    "file_id": file_id,
                    "prompt": request.prompt,
                    "model": self.model
                }
            )

        except Exception as e:
            logger.error(f"GigaChat image generation failed: {e}")
            raise

    async def _chat_completion(
        self,
        access_token: str,
        system_prompt: str,
        user_prompt: str
    ) -> Dict[str, Any]:
        """Send chat completion request"""
        url = f"{self.BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "function_call": "auto"
        }

        response = await self.http_client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    async def _download_image(self, access_token: str, file_id: str) -> bytes:
        """Download image by file_id"""
        url = f"{self.BASE_URL}/files/{file_id}/content"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await self.http_client.post(url, headers=headers)
        response.raise_for_status()
        return response.content

    def _build_system_prompt(self, request: ImageGenerationRequest) -> str:
        """Build system prompt for photorealistic medical images"""
        base = (
            "Ты - профессиональный художник, специализирующийся на создании "
            "фотореалистичных изображений для медицинских новостей. "
            "Твои изображения должны быть: "
            "1) Фотографического качества (как Canon EOS или Nikon) "
            "2) С естественным дневным освещением "
            "3) Реалистичные текстуры и материалы "
            "4) Документальный стиль National Geographic "
            "5) Без иллюстраций, мультяшности, 3D рендера"
        )

        if request.style_instructions:
            base += f"\n\nДополнительные инструкции: {request.style_instructions}"

        return base

    def _extract_file_id(self, chat_response: Dict[str, Any]) -> str:
        """Extract file_id from chat completion response"""
        try:
            content = chat_response["choices"][0]["message"]["content"]
            # Parse: <img src="{file_id}" fuse="true"/>
            import re
            match = re.search(r'src="([^"]+)"', content)
            if match:
                return match.group(1)
            raise ValueError("No file_id found in response")
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid response format: {e}")

    async def health_check(self) -> bool:
        """Check if GigaChat API is accessible"""
        try:
            access_token = await self.auth_manager.get_access_token()
            return bool(access_token)
        except Exception:
            return False
```

---

## 4. Migration Plan

### 4.1 Phase 1: Preparation (Week 1)

**Tasks:**
1. ✅ Analyze current Yandex Cloud ML implementation
2. ✅ Research GigaChat API documentation
3. ✅ Design unified provider interface
4. ⏳ Set up GigaChat API credentials in production
5. ⏳ Create test environment with both providers

**Deliverables:**
- Migration plan document (this file)
- GigaChat API credentials configured
- Test account setup

### 4.2 Phase 2: Implementation (Week 2-3)

**Tasks:**
1. Implement `GigaChatAuthManager` with token auto-refresh
2. Implement `GigaChatService` with Kandinsky 3.1 integration
3. Create `AIImageProvider` abstract interface
4. Refactor existing Yandex Cloud ML to use provider interface
5. Update `backend/api/image_generation.py` to support provider selection
6. Add configuration option `IMAGE_PROVIDER` (yandex|gigachat|both)

**Code changes:**
```python
# backend/core/config.py
class Settings:
    # ... existing settings ...

    # GigaChat credentials
    GIGACHAT_CLIENT_ID: str = os.getenv("GIGACHAT_CLIENT_ID", "")
    GIGACHAT_AUTH_KEY: str = os.getenv("GIGACHAT_AUTH_KEY", "")
    GIGACHAT_SCOPE: str = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    GIGACHAT_MODEL: str = os.getenv("GIGACHAT_MODEL", "GigaChat-2")

    # Image provider selection
    IMAGE_PROVIDER: str = os.getenv("IMAGE_PROVIDER", "yandex")  # yandex|gigachat|both
```

**Deliverables:**
- All new services implemented
- Unit tests for GigaChat integration
- Integration tests for image generation workflow

### 4.3 Phase 3: Testing (Week 3-4)

**Test scenarios:**
1. **Token management:**
   - Token auto-refresh
   - Concurrent requests
   - Token expiration handling

2. **Image generation:**
   - Simple prompts (medical scenes)
   - Complex prompts (specific medical procedures)
   - Russian language prompts
   - Style customization

3. **Error handling:**
   - Network failures
   - Invalid credentials
   - Rate limiting
   - Malformed responses

4. **Performance:**
   - Generation latency (Yandex vs GigaChat)
   - Concurrent requests
   - Load testing

5. **Quality comparison:**
   - Side-by-side image quality
   - Prompt adherence
   - Medical accuracy

**Test environment:**
```bash
# .env.test
IMAGE_PROVIDER=both
GIGACHAT_CLIENT_ID=test-client-id
GIGACHAT_AUTH_KEY=test-auth-key

# Run A/B testing
pytest tests/test_image_generation_comparison.py
```

**Deliverables:**
- Test report with quality comparison
- Performance benchmarks
- Recommendations on provider selection

### 4.4 Phase 4: Gradual Rollout (Week 4-5)

**Strategy:** Blue-Green deployment with feature flag

**Step 1: Dual-provider mode**
```python
# backend/api/image_generation.py
@router.post("/generate")
async def generate_image(request: GenerateImageRequest, provider: str = "yandex"):
    if provider == "gigachat":
        service = gigachat_service
    elif provider == "yandex":
        service = yandex_service
    else:
        # Generate with both, return GigaChat, log comparison
        service = both_providers_service
```

**Step 2: A/B testing (10% traffic)**
- Route 10% of requests to GigaChat
- Monitor quality metrics
- Collect user feedback

**Step 3: Gradual increase**
- 25% → 50% → 75% → 100%
- Monitor errors, latency, quality
- Rollback capability at any stage

**Step 4: Full migration**
- Switch default to GigaChat
- Keep Yandex as fallback for 2 weeks
- Remove Yandex provider after validation

**Deliverables:**
- Production deployment with feature flag
- Monitoring dashboard
- Rollback plan

### 4.5 Phase 5: Cleanup (Week 6)

**Tasks:**
1. Remove Yandex Cloud ML dependency
2. Clean up old configuration variables
3. Update documentation
4. Archive migration materials

**Code cleanup:**
```bash
# Remove dependency
pip uninstall yandex-cloud-ml-sdk

# Remove from requirements.txt
# yandex-cloud-ml-sdk==0.2.0  # REMOVED

# Remove old environment variables
# YC_FOLDER_ID  # REMOVED
# YC_API_KEY    # REMOVED
```

**Deliverables:**
- Clean codebase
- Updated documentation
- Post-migration report

---

## 5. Configuration Changes

### 5.1 New Environment Variables

**Required:**
```bash
# GigaChat credentials (from https://developers.sber.ru/portal/products/gigachat-api)
GIGACHAT_CLIENT_ID=019a1d13-7bbb-71d0-807b-2c567593ba93
GIGACHAT_AUTH_KEY=<base64-encoded-authorization-key>
GIGACHAT_SCOPE=GIGACHAT_API_PERS

# Provider selection
IMAGE_PROVIDER=gigachat  # yandex|gigachat|both
```

**Optional:**
```bash
# Model selection (default: GigaChat-2)
GIGACHAT_MODEL=GigaChat-2  # GigaChat-2|GigaChat-2-Pro|GigaChat-2-Max

# Token refresh buffer (minutes before expiration, default: 5)
GIGACHAT_TOKEN_REFRESH_BUFFER=5

# Timeout for API requests (seconds, default: 60)
GIGACHAT_REQUEST_TIMEOUT=60
```

### 5.2 Deprecated Environment Variables

**To be removed after migration:**
```bash
YC_FOLDER_ID      # Yandex Cloud Folder ID
YC_API_KEY        # Yandex Cloud API Key
```

---

## 6. API Compatibility

### 6.1 Endpoint Changes

**No breaking changes to public API!**

Existing endpoints remain unchanged:
- `POST /api/image-generation/generate`
- `POST /api/image-generation/upload`
- `GET /api/image-generation/health`
- `GET /api/image-generation/status`

### 6.2 Request/Response Format

**Request format:** No changes
```json
{
  "prompt": "Врач проводит УЗИ беременной женщине",
  "width_ratio": 1,
  "height_ratio": 1,
  "seed": null
}
```

**Response format:** Minor change in `model_used`
```json
{
  "image_url": "https://admin.news.rmevent.ru/images/{uuid}.jpeg",
  "model_used": "gigachat-kandinsky-3.1-GigaChat-2",  // CHANGED
  "success": true,
  "message": "Изображение успешно сгенерировано"
}
```

---

## 7. Risks & Mitigation

### 7.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Token expiration during long operations | High | Medium | Implement auto-refresh with buffer |
| GigaChat API rate limits | Medium | Low | Add rate limiting + retry logic |
| Image quality degradation | High | Low | A/B testing before full rollout |
| Network failures (Sberbank API) | Medium | Low | Fallback to Yandex for 2 weeks |
| Increased latency (2-step process) | Medium | Medium | Async processing + caching |

### 7.2 Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Higher API costs | Low | Unknown | Monitor costs during testing |
| Vendor lock-in (Sberbank) | Medium | High | Keep provider interface abstract |
| Service availability (bank infrastructure) | Medium | Low | Dual-provider mode during transition |

---

## 8. Success Metrics

### 8.1 Technical Metrics

- **Availability:** ≥99.5% uptime during rollout
- **Latency:** Image generation <30s (p95)
- **Error rate:** <2% failed generations
- **Token refresh:** 100% success rate

### 8.2 Quality Metrics

- **Image quality:** User satisfaction ≥4.5/5
- **Prompt adherence:** Manual review ≥90% accurate
- **Medical accuracy:** Expert review ≥95% appropriate

### 8.3 Cost Metrics

- **API cost:** Track cost per image (Yandex vs GigaChat)
- **Infrastructure:** No additional server costs

---

## 9. Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| 1. Preparation | Week 1 | ⏳ In Progress |
| 2. Implementation | Week 2-3 | ⏳ Pending |
| 3. Testing | Week 3-4 | ⏳ Pending |
| 4. Gradual Rollout | Week 4-5 | ⏳ Pending |
| 5. Cleanup | Week 6 | ⏳ Pending |

**Total estimated time:** 6 weeks
**Target completion:** December 2025

---

## 10. Next Steps

### Immediate Actions (This Week)

1. ✅ Complete this migration plan document
2. ⏳ Get approval from stakeholders
3. ⏳ Set up GigaChat API credentials (use provided Client ID and Auth Key)
4. ⏳ Create feature branch: `feature/gigachat-image-generation`
5. ⏳ Start implementing `GigaChatAuthManager`

### Questions for Stakeholders

1. **Budget:** What is the budget for API costs during testing?
2. **Timeline:** Is 6-week timeline acceptable?
3. **Quality:** What is minimum acceptable image quality vs Yandex?
4. **Fallback:** How long should we keep Yandex as fallback?
5. **Rollback:** What metrics trigger automatic rollback?

---

## Appendix A: GigaChat API Credentials

**From provided data:**
```
Client ID: 019a1d13-7bbb-71d0-807b-2c567593ba93
Scope: GIGACHAT_API_PERS
Authorization Key: <Получен 25.10.2025>
```

**OAuth endpoint:**
```
POST https://ngw.devices.sberbank.ru:9443/api/v2/oauth
```

**API base URL:**
```
https://gigachat.devices.sberbank.ru/api/v1
```

---

## Appendix B: Useful Resources

- **GigaChat Documentation:** https://developers.sber.ru/docs/ru/gigachat/api/reference
- **Image Generation Guide:** https://developers.sber.ru/docs/ru/gigachat/guides/images-generation
- **Python SDK:** https://github.com/ai-forever/gigachat
- **Postman Collection:** https://www.postman.com/salute-developers-7605/public/collection/17b9yp0/gigachat-api

---

**Document Version:** 1.0
**Last Updated:** 2025-10-30
**Author:** Development Team
**Status:** DRAFT - Awaiting Approval
