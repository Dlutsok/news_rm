# Medical News Automation System

Система автоматизации создания новостных материалов для медицинских платформ с поддержкой AI-генерации, RAG, многопроектности и Telegram-интеграции.

## 🚀 Возможности

- **AI-генерация контента** - автоматическое создание статей с помощью GPT-4
- **RAG система** - умный поиск и использование контекста через векторную БД (pgvector)
- **Многопроектность** - поддержка нескольких медицинских проектов (гинекология, педиатрия, терапия)
- **Парсинг новостей** - автоматический сбор из medvestnik.ru и других источников
- **Telegram интеграция** - публикация и управление через Telegram
- **Генерация изображений** - AI-генерация обложек через Yandex Cloud
- **Аналитика** - трекинг расходов на AI, статистика публикаций
- **Multi-user** - разграничение прав (admin/staff/analyst)

## 📋 Стек технологий

### Backend
- **FastAPI** - основной API сервер
- **PostgreSQL 14+** с **pgvector** - основная БД с векторным поиском
- **Redis** - кэширование и очереди
- **SQLModel** - ORM
- **Alembic** - миграции БД
- **Python 3.11+**

### Frontend
- **Next.js 13** (App Router)
- **React 18**
- **Tailwind CSS**
- **Framer Motion** - анимации
- **React Icons** (Feather)

### AI & ML
- **OpenAI GPT-4** - генерация текста
- **Yandex Cloud (YandexGPT)** - генерация изображений
- **Sentence Transformers** - embeddings для RAG
- **LangChain** - AI pipeline

### DevOps
- **Docker** & **Docker Compose**
- **Nginx** - reverse proxy с SSL
- **Let's Encrypt** - SSL сертификаты
- **Git hooks** - автодеплой

## 🏗️ Архитектура

```
┌─────────────────┐
│   Nginx + SSL   │  ← HTTPS (admin.news.rmevent.ru)
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
┌───▼───┐  ┌──▼─────┐
│ Next  │  │ FastAPI│
│  :3000│  │  :8000 │
└───┬───┘  └───┬────┘
    │          │
    │      ┌───▼────────┐
    │      │ PostgreSQL │
    │      │  +pgvector │
    │      └───┬────────┘
    │          │
    └──────────▼──────────┐
           Services:       │
    • News Parser          │
    • AI Generator         │
    • Image Service        │
    • Telegram Bot         │
    • RAG Pipeline         │
    └───────────────────────┘
```

## 📦 Быстрый старт

### Требования
- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 14+ (с pgvector)
- Node.js 18+ (для локальной разработки)
- Python 3.11+ (для локальной разработки)

### Локальная разработка

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd medical-news-automation

# 2. Настроить окружение
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local

# 3. Заполнить .env (API ключи, БД и т.д.)
nano .env

# 4. Запустить БД
docker-compose up -d db

# 5. Backend (в отдельном терминале)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload

# 6. Frontend (в отдельном терминале)
cd frontend
npm install
npm run dev
```

Приложение будет доступно:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Продакшн деплой

**См. подробное руководство:** [`deployed/DEPLOYMENT_GUIDE.md`](deployed/DEPLOYMENT_GUIDE.md)

```bash
# На продакшн сервере
cd /var/www/medical-news

# Скопировать prod конфиги
cp deployed/.env .env
cp deployed/frontend.env frontend/.env.production

# Запустить
./deployed/deploy.sh
```

### Автоматический деплой через Git

**См. CI/CD руководство:** [`deployed/CI-CD-GUIDE.md`](deployed/CI-CD-GUIDE.md)

```bash
# Настроить git hooks на сервере
./deployed/setup-git-hook.sh

# Теперь при git push изменения автоматически деплоятся!
```

## 📚 Документация

### Общая
- [`README.md`](README.md) - Этот файл
- [`docs/AUTH_SETUP.md`](docs/AUTH_SETUP.md) - Настройка аутентификации
- [`CODEOWNERS`](CODEOWNERS) - Ответственные за модули
- [`CLAUDE.md`](CLAUDE.md) - Инструкции для Claude Code

### Разработка
- [`docs/development/pre-change-checklist.md`](docs/development/pre-change-checklist.md) - Чеклист перед глобальными изменениями
- [`docs/templates/architecture-analysis-template.md`](docs/templates/architecture-analysis-template.md) - Шаблон архитектурного анализа
- [`.clinerules`](.clinerules) - Правила автоматизации для Claude Code

### Агенты
- [`.claude/agents/`](.claude/agents/) - Специализированные агенты Claude Code
- [`docs/agents-guide.md`](docs/agents-guide.md) - Руководство по работе с агентами
- [`docs/agents-technical-architect-reference.md`](docs/agents-technical-architect-reference.md) - Детальный справочник Technical Architect

### Deployment
- [`deployed/README.md`](deployed/README.md) - Быстрый старт
- [`deployed/DEPLOYMENT_GUIDE.md`](deployed/DEPLOYMENT_GUIDE.md) - Полное руководство
- [`deployed/CI-CD-GUIDE.md`](deployed/CI-CD-GUIDE.md) - Автодеплой

### API
- [`docs/api/`](docs/api/) - API документация
- http://localhost:8000/docs - Swagger UI (автодокументация)

### База данных
- [`docs/db/`](docs/db/) - Схема БД, миграции

### Архитектура
- [`docs/architecture/`](docs/architecture/) - Архитектурная документация
- [`docs/adr/`](docs/adr/) - Architecture Decision Records (ADR)

## 🔐 Безопасность

### Чувствительные данные

**ВАЖНО:** Никогда не коммитьте в git:
- `.env` файлы с реальными ключами
- `deployed/.env` и `deployed/frontend.env`
- Файлы с паролями и токенами

Используйте `.env.example` как шаблон.

### Учетные данные по умолчанию

**Локальная разработка:**
- Username: `admin`
- Password: `Adm1n-tr0ng_P@ssw0rd2024!`

**⚠️ Обязательно измените в продакшене!**

### API ключи

Необходимые API ключи (указать в `.env`):
- `OPENAI_API_KEY` - для GPT-4
- `YC_API_KEY` - для Yandex Cloud (генерация изображений)
- `TELEGRAM_BOT_TOKEN` - для Telegram бота

## 🛠️ Разработка

### Workflow с Technical Architect Agent

Перед внесением **глобальных изменений** в систему (новый функционал, рефакторинг, изменения архитектуры):

1. **Опишите изменение** используя триггерные фразы: "добавить функционал", "рефакторинг", "изменить архитектуру"
2. **Автоматически активируется Technical Architect Agent** (согласно `.clinerules`)
3. **TA Agent проведет анализ**:
   - Оценка влияния на компоненты
   - Построение графа зависимостей
   - Матрица рисков
   - План миграции
   - Стратегия отката
4. **Получите детальный отчет** с рекомендациями
5. **Team Lead (Claude) реализует** согласно плану

**Подробнее:**
- [Agents Guide](docs/agents-guide.md) - полное руководство по агентам
- [Technical Architect Reference](docs/agents-technical-architect-reference.md) - детальная документация TA Agent
- [Pre-Change Checklist](docs/development/pre-change-checklist.md) - чеклист перед изменениями
- [Architecture Analysis Template](docs/templates/architecture-analysis-template.md) - шаблон отчета

### Структура проекта

```
medical-news-automation/
├── .claude/              # 🤖 Claude Code конфигурация
│   └── agents/           # Специализированные агенты
│       └── technical-architect.md  # TA Agent для анализа изменений
├── backend/              # FastAPI приложение
│   ├── api/              # API endpoints
│   ├── core/             # Конфигурация, security
│   ├── database/         # Модели, схемы
│   ├── services/         # Бизнес-логика
│   ├── ai/               # AI сервисы (GPT, RAG, embeddings)
│   └── alembic/          # Миграции БД
├── frontend/             # Next.js приложение
│   ├── pages/            # Страницы
│   ├── components/       # React компоненты
│   ├── contexts/         # React контексты (Auth и т.д.)
│   └── utils/            # Утилиты, API клиент
├── deployed/             # Продакшн конфигурация
│   ├── .env              # Backend prod .env
│   ├── frontend.env      # Frontend prod .env
│   ├── docker-compose.yml
│   ├── nginx.conf
│   ├── deploy.sh         # Скрипт деплоя
│   └── git-deploy.sh     # Автодеплой
├── docs/                 # Документация
│   ├── architecture/     # Архитектурная документация
│   ├── adr/              # Architecture Decision Records
│   ├── api/              # API документация
│   ├── db/               # БД схема и миграции
│   ├── development/      # Руководства для разработчиков
│   │   └── pre-change-checklist.md  # Чеклист перед изменениями
│   └── templates/        # Шаблоны документов
│       └── architecture-analysis-template.md
├── scripts/              # Утилиты
├── .clinerules          # 🤖 Правила автоматизации Claude Code
├── CLAUDE.md            # Инструкции для Claude Code
└── docker-compose.yml   # Docker compose для разработки
```

### Миграции БД

```bash
# Создать миграцию
cd backend
alembic revision --autogenerate -m "Описание изменений"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1
```

### Тесты

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## 🐛 Troubleshooting

### CORS ошибки
```bash
# Проверить DEBUG режим
grep DEBUG .env

# Проверить CORS настройки
docker logs medical-news-backend | grep CORS
```

### База данных недоступна
```bash
# Проверить что PostgreSQL запущен
pg_isready -h localhost -p 5432

# Проверить соединение
psql -h localhost -U postgres -d news_aggregator
```

### Авторизация не работает
```bash
# Проверить JWT ключи одинаковые
grep JWT_SECRET_KEY .env

# Проверить логи
docker logs medical-news-backend | grep -i auth
```

**Подробнее:** [`deployed/DEPLOYMENT_GUIDE.md#troubleshooting`](deployed/DEPLOYMENT_GUIDE.md#troubleshooting)

## 📊 Мониторинг

### Логи

```bash
# Backend логи
docker logs medical-news-backend -f

# Frontend логи
docker logs medical-news-frontend -f

# Nginx логи
sudo tail -f /var/log/nginx/error.log
```

### Healthcheck

```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# Продакшн
curl https://admin.news.rmevent.ru/api/health
```

## 🤝 Contributing

1. Создайте feature branch (`git checkout -b feature/amazing-feature`)
2. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
3. Запушьте branch (`git push origin feature/amazing-feature`)
4. Откройте Pull Request

## 📝 Лицензия

Proprietary - все права защищены.

## 👥 Команда

- **Backend** - FastAPI, AI, RAG, Database
- **Frontend** - Next.js, UI/UX
- **DevOps** - Docker, Nginx, CI/CD

## 📧 Контакты

- Документация: `/docs/`
- API Docs: `/docs/api/`
- Issues: GitHub Issues
