# Архитектурный анализ: [Название изменения]

> **Шаблон для Technical Architect Agent**
>
> Заполните все секции этого шаблона при проведении архитектурного анализа.
> Удалите этот блок перед финальной версией отчета.

---

**Дата анализа**: YYYY-MM-DD
**Аналитик**: Technical Architect Agent
**Запросивший**: [Имя разработчика/Team Lead]
**Приоритет**: [CRITICAL / HIGH / MEDIUM / LOW]

---

## 📋 Executive Summary

> Краткое описание изменения и его влияния (2-3 предложения)

**Суть изменения**:
[Описать что меняется и почему]

**Главные риски**:
- Риск 1
- Риск 2

**Рекомендация**:
- [ ] ✅ Готов к реализации
- [ ] ⚠️ Готов с условиями (указать какими)
- [ ] ❌ Требует доработки плана

---

## 🎯 Цели изменения

### Бизнес-цели:
- [ ] Цель 1
- [ ] Цель 2
- [ ] Цель 3

### Технические цели:
- [ ] Цель 1
- [ ] Цель 2
- [ ] Цель 3

### Ожидаемые результаты:
- Результат 1
- Результат 2
- Результат 3

---

## 🔍 Current State Analysis

### Затрагиваемые компоненты:

#### Backend:
- **Модули**:
  - `backend/api/[module].py` - [описание]
  - `backend/services/[service].py` - [описание]
  - `backend/database/[models].py` - [описание]

- **API Endpoints**:
  - `GET /api/[endpoint]` - [статус: изменяется/новый/удаляется]
  - `POST /api/[endpoint]` - [статус: изменяется/новый/удаляется]

- **Database**:
  - Таблица `[table_name]` - [статус: изменяется/новая/удаляется]
  - ENUM тип `[enum_name]` - [статус: изменяется/новый/удаляется]

#### Frontend:
- **Pages**:
  - `frontend/pages/[page].js` - [описание влияния]

- **Components**:
  - `frontend/components/[Component].js` - [описание влияния]

- **Contexts**:
  - `frontend/contexts/[Context].js` - [описание влияния]

#### Integrations:
- **AI Services**: [описать влияние на OpenAI, Yandex Cloud]
- **Bitrix CMS**: [описать влияние на интеграцию]
- **Telegram**: [описать влияние на бота]
- **Парсеры**: [описать влияние на источники новостей]

#### Infrastructure:
- **Docker**: [требуются ли изменения в docker-compose.yml]
- **Nginx**: [требуются ли изменения в конфигурации]
- **Environment**: [новые переменные окружения]

### Текущие проблемы в затрагиваемых областях:

| Проблема | Критичность | Будет ли решена? |
|----------|-------------|------------------|
| Проблема 1 | High/Medium/Low | Да/Нет/Частично |
| Проблема 2 | High/Medium/Low | Да/Нет/Частично |

### Технический долг:

- **Существующий долг**: [описать текущий технический долг]
- **Влияние изменения**: [усугубит/уменьшит/не повлияет]
- **Рекомендации**: [что делать с техдолгом]

---

## 📊 Impact Analysis

### 🔴 High Impact Areas (Критичные области)

#### Область 1: [Название]
- **Компоненты**: [список]
- **Описание влияния**: [детальное описание]
- **Риски**: [конкретные риски]
- **Митигация**: [как снизить риски]

#### Область 2: [Название]
- **Компоненты**: [список]
- **Описание влияния**: [детальное описание]
- **Риски**: [конкретные риски]
- **Митигация**: [как снизить риски]

### 🟠 Medium Impact Areas (Средние области)

#### Область 1: [Название]
- **Влияние**: [описание]
- **Действия**: [что нужно сделать]

#### Область 2: [Название]
- **Влияние**: [описание]
- **Действия**: [что нужно сделать]

### 🟢 Low Impact Areas (Низкие области)

- Область 1: [краткое описание]
- Область 2: [краткое описание]

---

## 🕸️ Dependency Graph

### Визуальное представление:

```
[Изменяемый компонент]
    │
    ├── Прямые зависимости (что нужно компоненту)
    │   ├── Зависимость A
    │   │   └── Sub-зависимость A.1
    │   └── Зависимость B
    │
    ├── Обратные зависимости (кто использует компонент)
    │   ├── Компонент X
    │   │   ├── Влияние: [описание]
    │   │   └── Действие: [что нужно сделать]
    │   └── Компонент Y
    │       ├── Влияние: [описание]
    │       └── Действие: [что нужно сделать]
    │
    └── Побочные эффекты
        ├── Кэширование
        ├── Миграции БД
        ├── API версионирование
        └── Документация
```

### Детальный список зависимостей:

#### Прямые (Direct Dependencies):
1. **[Зависимость 1]**
   - Тип: [модуль/пакет/сервис]
   - Версия: [текущая версия]
   - Влияние: [как изменение влияет]

2. **[Зависимость 2]**
   - Тип: [модуль/пакет/сервис]
   - Версия: [текущая версия]
   - Влияние: [как изменение влияет]

#### Обратные (Reverse Dependencies):
1. **[Компонент 1]** использует изменяемый модуль
   - Файл: [путь к файлу]
   - Использование: [как использует]
   - **Требуется обновление**: Да/Нет
   - **Риск breaking change**: High/Medium/Low

2. **[Компонент 2]** использует изменяемый модуль
   - Файл: [путь к файлу]
   - Использование: [как использует]
   - **Требуется обновление**: Да/Нет
   - **Риск breaking change**: High/Medium/Low

---

## ⚠️ Risk Matrix

### Критичные риски (Critical):

| # | Риск | Вероятность | Критичность | Митигация | Ответственный |
|---|------|-------------|-------------|-----------|---------------|
| 1 | [Описание риска] | High/Medium/Low | Critical | [План митигации] | [Team Lead] |
| 2 | [Описание риска] | High/Medium/Low | Critical | [План митигации] | [Team Lead] |

### Высокие риски (High):

| # | Риск | Вероятность | Критичность | Митигация |
|---|------|-------------|-------------|-----------|
| 1 | [Описание риска] | High/Medium/Low | High | [План митигации] |
| 2 | [Описание риска] | High/Medium/Low | High | [План митигации] |

### Средние риски (Medium):

| # | Риск | Вероятность | Критичность | Митигация |
|---|------|-------------|-------------|-----------|
| 1 | [Описание риска] | High/Medium/Low | Medium | [План митигации] |

### Низкие риски (Low):

- Риск 1: [краткое описание]
- Риск 2: [краткое описание]

### Общий Risk Score:

**Formula**: (Количество Critical × 10) + (Количество High × 5) + (Количество Medium × 2) + (Количество Low × 1)

**Total Risk Score**: [число]

**Risk Level**:
- 0-10: 🟢 Low
- 11-25: 🟡 Medium
- 26-50: 🟠 High
- 51+: 🔴 Critical

---

## 🗺️ Migration Path

### Overview:
- **Общая длительность**: [X hours/days]
- **Сложность**: [Low/Medium/High/Critical]
- **Требуется downtime**: [Да/Нет, если да - сколько]
- **Rollback complexity**: [Easy/Medium/Hard]

---

### Phase 1: Preparation (Время: [X hours])

**Цель**: Подготовить окружение и создать безопасность для отката

#### Задачи:

- [ ] **1.1** Создать полный бэкап production БД
  - Команда: `pg_dump -U postgres news_aggregator > backup_$(date +%Y%m%d_%H%M%S).sql`
  - Проверка: Убедиться что backup файл создан и не пустой
  - Ответственный: [Team Lead]

- [ ] **1.2** Создать git branch для изменений
  - Команда: `git checkout -b feature/[feature-name]`
  - Ответственный: [Team Lead]

- [ ] **1.3** Обновить локальную документацию
  - Файлы: [список файлов для обновления]
  - Ответственный: [Team Lead]

- [ ] **1.4** Проверить staging окружение
  - Проверка: staging доступен и актуален
  - Ответственный: [Team Lead]

- [ ] **1.5** [Дополнительная задача]
  - Описание: [что сделать]
  - Ответственный: [Team Lead]

**Exit Criteria Phase 1**:
- ✅ Бэкапы созданы и проверены
- ✅ Branch создан
- ✅ Staging готов к тестированию

---

### Phase 2: Implementation (Время: [X hours])

**Цель**: Реализовать изменения согласно плану

#### Step 2.1: Database Changes (если применимо)

- [ ] **2.1.1** Создать Alembic миграцию
  ```bash
  cd backend
  alembic revision --autogenerate -m "[описание миграции]"
  ```

- [ ] **2.1.2** Проверить миграцию вручную
  - Файл: `backend/alembic/versions/[revision]_*.py`
  - Проверка: downgrade() метод присутствует и корректен

- [ ] **2.1.3** Применить миграцию локально
  ```bash
  alembic upgrade head
  ```

- [ ] **2.1.4** Проверить структуру БД
  ```sql
  \d+ [table_name]
  SELECT * FROM [table_name] LIMIT 5;
  ```

#### Step 2.2: Backend Changes

- [ ] **2.2.1** Обновить models.py
  - Файл: `backend/database/models.py`
  - Изменения: [описать конкретные изменения]

- [ ] **2.2.2** Обновить schemas.py (Pydantic)
  - Файл: `backend/database/schemas.py`
  - Изменения: [описать конкретные изменения]

- [ ] **2.2.3** Обновить/создать API endpoints
  - Файлы: `backend/api/[module].py`
  - Изменения: [описать конкретные изменения]

- [ ] **2.2.4** Обновить services
  - Файлы: `backend/services/[service].py`
  - Изменения: [описать конкретные изменения]

- [ ] **2.2.5** Добавить/обновить middleware (если нужно)
  - Файл: `backend/middleware/[middleware].py`
  - Изменения: [описать конкретные изменения]

#### Step 2.3: Frontend Changes (если применимо)

- [ ] **2.3.1** Обновить API client
  - Файл: `frontend/utils/api.js`
  - Изменения: [описать конкретные изменения]

- [ ] **2.3.2** Обновить/создать components
  - Файлы: `frontend/components/[Component].js`
  - Изменения: [описать конкретные изменения]

- [ ] **2.3.3** Обновить pages
  - Файлы: `frontend/pages/[page].js`
  - Изменения: [описать конкретные изменения]

- [ ] **2.3.4** Обновить contexts (если нужно)
  - Файл: `frontend/contexts/[Context].js`
  - Изменения: [описать конкретные изменения]

#### Step 2.4: Integration Changes (если применимо)

- [ ] **2.4.1** Обновить AI сервисы
  - Файлы: [список файлов]
  - Изменения: [описать конкретные изменения]

- [ ] **2.4.2** Обновить Bitrix интеграцию
  - Файлы: [список файлов]
  - Изменения: [описать конкретные изменения]

- [ ] **2.4.3** Обновить Telegram бота
  - Файлы: [список файлов]
  - Изменения: [описать конкретные изменения]

**Checkpoint 2.1**: Локальное тестирование
- Запустить backend: `cd backend && uvicorn main:app --reload`
- Запустить frontend: `cd frontend && npm run dev`
- Проверить что изменения работают локально

**Exit Criteria Phase 2**:
- ✅ Код написан и работает локально
- ✅ Линтеры проходят без ошибок
- ✅ Нет TODO/FIXME в critical местах

---

### Phase 3: Validation (Время: [X hours])

**Цель**: Протестировать изменения на всех уровнях

#### Step 3.1: Unit Tests

- [ ] **3.1.1** Написать/обновить backend unit tests
  ```bash
  cd backend
  pytest tests/test_[module].py -v
  ```
  - Файлы: [список тестовых файлов]
  - Coverage: >= 70%

- [ ] **3.1.2** Написать/обновить frontend unit tests
  ```bash
  cd frontend
  npm test
  ```
  - Файлы: [список тестовых файлов]

#### Step 3.2: Integration Tests

- [ ] **3.2.1** Тест API endpoints
  - Инструмент: Postman/curl/httpx
  - Endpoints: [список для тестирования]

- [ ] **3.2.2** Тест БД операций
  - Проверка: CRUD операции работают корректно
  - Проверка: Foreign keys корректно работают

- [ ] **3.2.3** Тест интеграций с внешними сервисами
  - AI сервисы: [тесты]
  - Bitrix: [тесты]
  - Telegram: [тесты]

#### Step 3.3: E2E Tests

- [ ] **3.3.1** Сценарий 1: [Название сценария]
  - Шаги: [детальные шаги теста]
  - Ожидаемый результат: [описание]

- [ ] **3.3.2** Сценарий 2: [Название сценария]
  - Шаги: [детальные шаги теста]
  - Ожидаемый результат: [описание]

#### Step 3.4: Staging Deployment & Testing

- [ ] **3.4.1** Deploy на staging
  ```bash
  git push origin feature/[feature-name]
  # SSH на staging сервер
  ./deploy_staging.sh
  ```

- [ ] **3.4.2** Применить миграции на staging
  ```bash
  cd backend
  alembic upgrade head
  ```

- [ ] **3.4.3** Проверить health endpoints
  ```bash
  curl https://staging.api.url/health
  curl https://staging.api.url/api/health
  ```

- [ ] **3.4.4** Manual QA на staging
  - [ ] Проверка UI/UX
  - [ ] Проверка критичных функций
  - [ ] Проверка edge cases
  - [ ] Проверка error handling

- [ ] **3.4.5** Performance тестирование
  - Response time: [результаты]
  - Memory usage: [результаты]
  - DB query time: [результаты]

- [ ] **3.4.6** Security тестирование (если применимо)
  - SQL injection: проверен
  - XSS: проверен
  - CSRF: проверен
  - Rate limiting: проверен

**Exit Criteria Phase 3**:
- ✅ Все тесты проходят
- ✅ Staging работает стабильно
- ✅ Performance приемлемый
- ✅ Нет критичных багов

---

### Phase 4: Documentation (Время: [X minutes])

**Цель**: Обновить всю документацию

- [ ] **4.1** Обновить `CHANGELOG.md`
  - Добавить запись об изменениях
  - Указать breaking changes (если есть)
  - Указать новые features

- [ ] **4.2** Обновить `docs/api/endpoints.md` (если применимо)
  - Добавить новые endpoints
  - Обновить измененные endpoints
  - Добавить примеры запросов/ответов

- [ ] **4.3** Обновить `docs/db/schema.md` (если применимо)
  - Обновить структуру таблиц
  - Добавить новые индексы
  - Обновить ENUM типы

- [ ] **4.4** Создать ADR (если архитектурное решение)
  - Файл: `docs/adr/ADR-[number]-[title].md`
  - Содержание: Context, Decision, Consequences

- [ ] **4.5** Обновить `docs/architecture/overview.md` (если применимо)
  - Обновить диаграммы
  - Обновить описание компонентов

- [ ] **4.6** Обновить `CLAUDE.md` (если изменились dev команды)
  - Обновить команды разработки
  - Обновить архитектурные заметки

- [ ] **4.7** Обновить `README.md` (если изменился getting started)
  - Обновить инструкции по установке
  - Обновить требования к окружению

**Exit Criteria Phase 4**:
- ✅ Вся документация обновлена
- ✅ ADR создан (если нужно)
- ✅ Changelog актуален

---

### Phase 5: Production Deployment (Время: [X minutes])

**Цель**: Безопасно задеплоить изменения на production

#### Pre-Deployment Checklist:

- [ ] **5.0.1** Все предыдущие фазы завершены успешно
- [ ] **5.0.2** Staging работает стабильно минимум 24 часа
- [ ] **5.0.3** Rollback план подготовлен и проверен
- [ ] **5.0.4** Мониторинг настроен
- [ ] **5.0.5** Команда готова к мониторингу после деплоя

#### Deployment Steps:

- [ ] **5.1** Создать production бэкап прямо перед деплоем
  ```bash
  ssh production-server
  pg_dump -U postgres news_aggregator > backup_pre_deploy_$(date +%Y%m%d_%H%M%S).sql
  ```

- [ ] **5.2** Merge в main branch
  ```bash
  git checkout main
  git merge feature/[feature-name]
  git push origin main
  ```

- [ ] **5.3** Deploy на production
  ```bash
  ssh production-server
  cd /path/to/project
  git pull origin main
  ./deploy.sh
  ```

- [ ] **5.4** Применить БД миграции (если есть)
  ```bash
  cd backend
  alembic upgrade head
  ```

- [ ] **5.5** Restart services
  ```bash
  docker-compose restart backend
  docker-compose restart frontend
  # или
  systemctl restart medical-news-backend
  systemctl restart medical-news-frontend
  ```

- [ ] **5.6** Verify deployment
  ```bash
  curl https://api.production.url/health
  docker logs medical-news-backend --tail=100
  docker logs medical-news-frontend --tail=100
  ```

#### Post-Deployment Monitoring (First 30 minutes):

- [ ] **5.7** Мониторинг логов (первые 5 минут)
  - Backend logs: нет errors
  - Frontend logs: нет errors
  - Nginx logs: нет 5xx ошибок

- [ ] **5.8** Проверка метрик (первые 15 минут)
  - CPU usage: в норме
  - Memory usage: в норме
  - DB connections: в норме
  - API response time: в норме

- [ ] **5.9** Manual smoke tests (первые 15 минут)
  - [ ] Авторизация работает
  - [ ] Парсинг новостей работает
  - [ ] AI генерация работает
  - [ ] Публикация в Bitrix работает
  - [ ] Telegram posting работает
  - [ ] Все 3 проекта (GS, PS, TS) работают

- [ ] **5.10** Проверка алертов
  - Нет критичных алертов от мониторинга

#### Post-Deployment Actions:

- [ ] **5.11** Уведомить команду об успешном деплое
- [ ] **5.12** Добавить заметку в deployment log
- [ ] **5.13** Закрыть связанные issues/tickets
- [ ] **5.14** Запланировать post-mortem (для критичных изменений)

**Exit Criteria Phase 5**:
- ✅ Deployment успешен
- ✅ Все services работают
- ✅ Мониторинг показывает норму
- ✅ Manual tests пройдены

---

## 🔙 Rollback Strategy

### Когда откатывать

**Immediate Rollback Triggers** (откатывать немедленно):
- 🔴 Production downtime (недоступность сервиса)
- 🔴 Data loss обнаружен
- 🔴 Security breach
- 🔴 Database corruption

**High Priority Rollback Triggers** (откатывать ASAP):
- 🟠 Критичные функции не работают
- 🟠 >50% пользователей не могут авторизоваться
- 🟠 AI сервисы полностью недоступны
- 🟠 Публикация не работает для всех проектов

**Consider Rollback Triggers** (оценить и решить):
- 🟡 Существенное падение performance (>3x slower)
- 🟡 Некритичные ошибки в логах
- 🟡 Проблемы с одним проектом (GS/PS/TS)

### Rollback Steps

#### Quick Rollback (для code-only changes):

```bash
# 1. SSH на production сервер
ssh production-server

# 2. Откатить код на предыдущий коммит
cd /path/to/project
git log --oneline -5  # найти предыдущий коммит
git reset --hard [previous-commit-hash]

# 3. Restart services
docker-compose restart backend frontend
# или
systemctl restart medical-news-backend medical-news-frontend

# 4. Проверить что откат успешен
curl https://api.production.url/health
docker logs medical-news-backend --tail=50
```

#### Full Rollback (для changes с БД миграциями):

```bash
# 1. Остановить services
docker-compose down
# или
systemctl stop medical-news-backend medical-news-frontend

# 2. Откатить БД миграцию
cd backend
alembic downgrade -1  # или конкретную revision
# Проверить: alembic current

# 3. Откатить код
git reset --hard [previous-commit-hash]

# 4. Restart services
docker-compose up -d
# или
systemctl start medical-news-backend medical-news-frontend

# 5. Verify
curl https://api.production.url/health
psql -U postgres -d news_aggregator -c "SELECT version_num FROM alembic_version;"
```

#### Emergency Full Restore (в крайнем случае):

```bash
# 1. Остановить все services
docker-compose down

# 2. Восстановить БД из бэкапа
psql -U postgres -d postgres -c "DROP DATABASE news_aggregator;"
psql -U postgres -d postgres -c "CREATE DATABASE news_aggregator;"
psql -U postgres -d news_aggregator < backup_pre_deploy_[timestamp].sql

# 3. Откатить код на known-good version
git reset --hard [known-good-commit]

# 4. Restart services
docker-compose up -d

# 5. Verify
./scripts/verify_system_health.sh
```

### Post-Rollback Actions:

- [ ] Уведомить команду о rollback
- [ ] Задокументировать причину rollback
- [ ] Создать incident report
- [ ] Запланировать post-mortem
- [ ] Проанализировать что пошло не так
- [ ] Обновить план для следующей попытки

### Rollback Testing:

**Перед production deployment протестировать rollback на staging**:
```bash
# На staging сервере
cd /path/to/project
git log --oneline -5
git reset --hard [previous-commit]
alembic downgrade -1
# Проверить что все работает
```

---

## 🧪 Testing Requirements

### Unit Tests

#### Backend Tests (pytest):

**Новые тесты**:
- [ ] `tests/test_[module].py::test_[function_name]`
  - Описание: [что тестирует]
  - Coverage: [%]

- [ ] `tests/test_[module].py::test_[function_name]_edge_case`
  - Описание: [что тестирует]
  - Coverage: [%]

**Обновленные тесты**:
- [ ] `tests/test_[existing_module].py`
  - Изменения: [что изменилось в тестах]

**Команды для запуска**:
```bash
cd backend
pytest tests/test_[module].py -v --cov
```

**Expected Coverage**: >= 70% для новых модулей

#### Frontend Tests (Jest):

**Новые тесты**:
- [ ] `components/[Component].test.js`
  - Описание: [что тестирует]

- [ ] `utils/[utility].test.js`
  - Описание: [что тестирует]

**Команды для запуска**:
```bash
cd frontend
npm test -- --coverage
```

---

### Integration Tests

#### API Integration Tests:

- [ ] **Test 1**: [Название теста]
  - Endpoint: `[METHOD] /api/[endpoint]`
  - Request:
    ```json
    {
      "field": "value"
    }
    ```
  - Expected Response:
    ```json
    {
      "status": "success",
      "data": {...}
    }
    ```
  - Edge Cases: [список edge cases для проверки]

- [ ] **Test 2**: [Название теста]
  - [аналогично Test 1]

#### Database Integration Tests:

- [ ] **Test 1**: CRUD операции для [table_name]
  - Create: успешно создается запись
  - Read: успешно читается запись
  - Update: успешно обновляется запись
  - Delete: успешно удаляется запись

- [ ] **Test 2**: Foreign Key constraints
  - Проверка: FK работают корректно
  - Проверка: ON DELETE CASCADE работает (если есть)

#### External Services Integration Tests:

- [ ] **OpenAI Integration**
  - Тест: генерация текста работает
  - Тест: tracking расходов работает
  - Edge case: обработка ошибок API

- [ ] **Bitrix Integration**
  - Тест: публикация статьи работает
  - Тест: загрузка изображения работает
  - Edge case: обработка ошибок API

- [ ] **Telegram Integration**
  - Тест: отправка поста работает
  - Edge case: rate limiting работает

---

### E2E Tests (End-to-End)

#### Scenario 1: [Название сценария]

**User Story**: Как [роль], я хочу [действие], чтобы [результат]

**Preconditions**:
- Пользователь авторизован как [роль]
- В системе есть [данные]

**Steps**:
1. Открыть страницу [URL]
2. Кликнуть на [элемент]
3. Заполнить форму:
   - Поле 1: [значение]
   - Поле 2: [значение]
4. Нажать кнопку [название]
5. Дождаться [результата]

**Expected Result**:
- Отображается [UI элемент]
- Данные сохранены в БД
- Уведомление показано пользователю

**Edge Cases to Test**:
- [ ] Валидация полей работает
- [ ] Обработка ошибок сервера
- [ ] Loading states отображаются

#### Scenario 2: [Название сценария]
[аналогично Scenario 1]

---

### Performance Tests

#### Load Testing:

- [ ] **Test 1**: Concurrent API requests
  - Tool: Apache JMeter / Locust
  - Scenario: [X] concurrent users
  - Endpoint: `[METHOD] /api/[endpoint]`
  - Expected: Response time < 500ms (95 percentile)

- [ ] **Test 2**: Database query performance
  - Query: `SELECT ...`
  - Expected: Execution time < 100ms

#### Stress Testing (если применимо):

- [ ] Максимальная нагрузка на [компонент]
  - Current capacity: [X req/sec]
  - Target capacity: [Y req/sec]
  - Result: [passed/failed]

---

### Security Tests (если применимо)

#### Authentication & Authorization:

- [ ] **Test 1**: JWT token validation
  - Проверка: Invalid token отклоняется
  - Проверка: Expired token отклоняется
  - Проверка: Valid token принимается

- [ ] **Test 2**: CSRF protection
  - Проверка: Запросы без CSRF токена отклоняются
  - Проверка: Запросы с invalid CSRF токеном отклоняются

#### Input Validation:

- [ ] **Test 1**: SQL Injection prevention
  - Payload: `' OR '1'='1`
  - Expected: Request rejected / sanitized

- [ ] **Test 2**: XSS prevention
  - Payload: `<script>alert('XSS')</script>`
  - Expected: Payload escaped / sanitized

#### Rate Limiting:

- [ ] **Test 1**: Rate limit на [endpoint]
  - Limit: [X requests per minute]
  - Test: Отправить [X+1] requests
  - Expected: 429 Too Many Requests после [X] запросов

---

## 📚 Documentation Updates

### Обязательные обновления:

- [ ] **`CHANGELOG.md`**
  - Раздел: `## [Version] - YYYY-MM-DD`
  - Добавить:
    - **Added**: [список новых features]
    - **Changed**: [список изменений]
    - **Fixed**: [список исправленных багов]
    - **Breaking Changes**: [список breaking changes]

- [ ] **`docs/api/endpoints.md`** (если изменяется API)
  - Обновить таблицу endpoints
  - Добавить примеры запросов/ответов для новых endpoints
  - Обновить описание измененных endpoints
  - Отметить deprecated endpoints

- [ ] **`docs/db/schema.md`** (если изменяется БД)
  - Обновить ERD диаграмму
  - Обновить описание таблиц
  - Добавить информацию о новых индексах
  - Обновить ENUM типы
  - Добавить информацию о миграциях

- [ ] **`docs/adr/ADR-[number]-[title].md`** (для архитектурных решений)
  - Шаблон ADR:
    ```markdown
    # ADR-[number]: [Title]

    **Status**: [Proposed/Accepted/Deprecated/Superseded]
    **Date**: YYYY-MM-DD
    **Authors**: [Имена]

    ## Context
    [Описание проблемы и контекста]

    ## Decision
    [Описание принятого решения]

    ## Consequences
    [Положительные и отрицательные последствия]

    ## Alternatives Considered
    [Альтернативные решения]
    ```

### Рекомендуемые обновления:

- [ ] **`docs/architecture/overview.md`** (если меняется архитектура)
  - Обновить диаграммы компонентов
  - Обновить описание взаимодействий
  - Добавить новые компоненты

- [ ] **`CLAUDE.md`** (если меняются dev команды)
  - Обновить команды разработки
  - Обновить архитектурные заметки
  - Добавить новые соглашения

- [ ] **`README.md`** (если меняется getting started)
  - Обновить инструкции по установке
  - Обновить требования к окружению
  - Обновить примеры использования

- [ ] **`docs/runbooks/deployment.md`** (если меняется процесс деплоя)
  - Обновить шаги деплоя
  - Добавить новые проверки
  - Обновить rollback инструкции

### Проверка качества документации:

- [ ] Вся документация написана понятным языком
- [ ] Примеры кода актуальны и работают
- [ ] Скриншоты обновлены (если есть)
- [ ] Ссылки между документами корректны
- [ ] Нет broken links
- [ ] Markdown форматирование корректно

---

## 🚀 Recommendations

### Must Have (Обязательно выполнить):

1. **[Рекомендация 1]**
   - Приоритет: Critical
   - Описание: [детальное описание]
   - Обоснование: [почему это критично]

2. **[Рекомендация 2]**
   - Приоритет: High
   - Описание: [детальное описание]
   - Обоснование: [почему это важно]

### Nice to Have (Желательно выполнить):

1. **[Рекомендация 1]**
   - Приоритет: Medium
   - Описание: [детальное описание]
   - Польза: [какую пользу принесет]

2. **[Рекомендация 2]**
   - Приоритет: Low
   - Описание: [детальное описание]
   - Польза: [какую пользу принесет]

### Future Considerations (Для будущих итераций):

1. **[Идея 1]**
   - Описание: [что можно улучшить в будущем]
   - Estimated effort: [X hours/days]

2. **[Идея 2]**
   - Описание: [что можно улучшить в будущем]
   - Estimated effort: [X hours/days]

### Technical Debt Items:

- **Debt 1**: [Описание технического долга который создается/остается]
  - Impact: High/Medium/Low
  - Рекомендация: [когда и как исправить]

- **Debt 2**: [Описание технического долга который создается/остается]
  - Impact: High/Medium/Low
  - Рекомендация: [когда и как исправить]

---

## ✅ Pre-flight Checklist

**Финальная проверка перед началом реализации**:

### Анализ:
- [ ] TA Agent анализ завершен и одобрен
- [ ] Все риски идентифицированы и есть митигация
- [ ] Граф зависимостей построен и проанализирован
- [ ] Impact analysis проведен для всех компонентов

### Подготовка:
- [ ] Бэкап production БД создан
- [ ] Rollback план подготовлен и проверен
- [ ] Staging окружение готово к тестированию
- [ ] Все зависимости проверены (версии, доступность)

### Тестирование:
- [ ] Тестовые сценарии написаны
- [ ] Unit тесты подготовлены
- [ ] Integration тесты подготовлены
- [ ] E2E тесты подготовлены

### Документация:
- [ ] План миграции детально расписан
- [ ] Документация подготовлена для обновления
- [ ] ADR drafted (если архитектурное решение)
- [ ] Changelog entry подготовлен

### Команда:
- [ ] Team Lead готов к реализации
- [ ] Ответственные за мониторинг назначены
- [ ] Время деплоя согласовано (если критично)
- [ ] Communication plan подготовлен

---

## 👥 Team Lead Handoff

### Готовность к реализации:

**Status**:
- [ ] ✅ READY - Готов к немедленной реализации
- [ ] ⚠️ READY WITH CONDITIONS - Готов с условиями (см. ниже)
- [ ] ❌ NOT READY - Требуется доработка плана
- [ ] 🔄 NEEDS REVIEW - Требуется дополнительный ревью

**Приоритет**:
- [ ] 🔴 CRITICAL - Немедленная реализация required
- [ ] 🟠 HIGH - Реализовать в течение 1-2 дней
- [ ] 🟡 MEDIUM - Реализовать в течение недели
- [ ] 🟢 LOW - Можно отложить

### Рекомендуемая последовательность реализации:

1. **[Шаг 1]**: [Краткое описание]
   - Файлы: [список основных файлов]
   - Время: [оценка времени]
   - Риск: Low/Medium/High

2. **[Шаг 2]**: [Краткое описание]
   - Файлы: [список основных файлов]
   - Время: [оценка времени]
   - Риск: Low/Medium/High

3. **[Шаг 3]**: [Краткое описание]
   - Файлы: [список основных файлов]
   - Время: [оценка времени]
   - Риск: Low/Medium/High

### Особые указания для Team Lead:

**Critical Points** (обратить особое внимание):
1. [Критичная точка 1]: [детальное описание]
2. [Критичная точка 2]: [детальное описание]

**Common Pitfalls** (типичные ошибки чтобы избежать):
1. [Подводный камень 1]: [как избежать]
2. [Подводный камень 2]: [как избежать]

**Testing Focus Areas** (на что обратить особое внимание при тестировании):
1. [Область 1]: [почему важно]
2. [Область 2]: [почему важно]

### Conditions (если READY WITH CONDITIONS):

**Условия которые должны быть выполнены**:
1. [ ] [Условие 1]
2. [ ] [Условие 2]
3. [ ] [Условие 3]

### Estimated Timeline:

- **Analysis & Planning**: [уже завершено] ✅
- **Implementation**: [X hours]
- **Testing**: [X hours]
- **Documentation**: [X minutes]
- **Deployment**: [X minutes]
- **Post-deployment monitoring**: 30 minutes

**Total Estimated Time**: [X hours/days]

### Resources Needed:

- **People**: [кто нужен из команды]
- **Tools**: [какие инструменты понадобятся]
- **Access**: [какие доступы нужны]
- **Services**: [какие внешние сервисы]

### Communication Plan:

- **Stakeholders to notify**: [кого уведомить]
- **Notification timing**: [когда уведомлять]
- **Channels**: [через какие каналы]

---

## 📊 Success Criteria

**Изменение считается успешным если**:

### Technical Success:
- [ ] Все тесты проходят (unit, integration, e2e)
- [ ] Production деплой прошел без rollback
- [ ] Нет критичных bugs в течение 48 часов
- [ ] Performance метрики в пределах нормы
- [ ] Нет security issues

### Business Success:
- [ ] Цели изменения достигнуты
- [ ] Пользователи могут использовать новую функциональность
- [ ] Нет негативного impact на существующие функции
- [ ] Все 3 проекта (GS, PS, TS) работают корректно

### Documentation Success:
- [ ] Вся документация обновлена
- [ ] ADR создан (если нужно)
- [ ] Runbooks актуальны
- [ ] Changelog обновлен

### Team Success:
- [ ] Команда понимает изменения
- [ ] Знания передал (knowledge sharing)
- [ ] Lessons learned задокументированы

---

## 📝 Notes & Additional Context

### Assumptions Made:

1. [Assumption 1]: [описание предположения]
2. [Assumption 2]: [описание предположения]

### Open Questions:

1. **[Question 1]**: [вопрос который требует clarification]
   - Priority: High/Medium/Low
   - Assigned to: [кто должен ответить]

2. **[Question 2]**: [вопрос который требует clarification]
   - Priority: High/Medium/Low
   - Assigned to: [кто должен ответить]

### Related Work:

- **Issue #[number]**: [ссылка и краткое описание]
- **PR #[number]**: [ссылка и краткое описание]
- **ADR-[number]**: [ссылка и краткое описание]

### External Dependencies:

1. **[Dependency 1]**: [описание зависимости от внешнего фактора]
   - Status: [available/pending/blocked]
   - ETA: [когда будет готово]

2. **[Dependency 2]**: [описание зависимости от внешнего фактора]
   - Status: [available/pending/blocked]
   - ETA: [когда будет готово]

---

**Report Version**: 1.0
**Generated by**: Technical Architect Agent
**Report Date**: YYYY-MM-DD HH:MM
**Last Updated**: YYYY-MM-DD HH:MM

---

## 🔄 Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | YYYY-MM-DD | TA Agent | Initial analysis |
| 1.1 | YYYY-MM-DD | TA Agent | Updated based on feedback |

---

**END OF ARCHITECTURE ANALYSIS REPORT**
