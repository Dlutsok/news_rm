# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Medical News Automation System** - A full-stack medical news aggregation platform with AI-powered content generation, multi-project support (Gynecology, Pediatrics, Therapy schools), and automated publishing to Bitrix CMS and Telegram.

## Tech Stack

### Backend (FastAPI)
- **Python 3.11+** with FastAPI, SQLModel, Alembic
- **PostgreSQL 14+** with pgvector extension (for RAG/embeddings)
- **AI Services**: OpenAI GPT-4, Yandex Cloud ML (image generation), Sentence Transformers
- **Authentication**: JWT tokens with HttpOnly cookies, CSRF protection
- **News Sources**: Medvestnik, RIA, AIG, Remedium, RBC Medical parsers

### Frontend (Next.js)
- **Next.js 14** with App Router
- **React 18**, Tailwind CSS, Framer Motion
- **Rich Text Editor**: React Quill
- **Icons**: React Icons (Feather)

### Infrastructure
- **Docker Compose** for orchestration
- **Nginx** reverse proxy with SSL (Let's Encrypt)
- **Daily auto-parsing** at 02:00 Moscow time
- **External cron** for scheduled publishing

## Development Commands

### Backend Development
```bash
cd backend

# Local development with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Create database migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Run tests
pytest

# Create admin user
python create_user.py

# Reset admin password
python reset_admin_password.py
```

### Frontend Development
```bash
cd frontend

# Local development
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint
npm run lint
```

### Docker Commands
```bash
# Start all services (production)
docker-compose up -d

# View logs
docker logs medical-news-backend -f
docker logs medical-news-frontend -f

# Restart service
docker-compose restart backend
docker-compose restart frontend

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Deployment
```bash
# Deploy to production (from deployed/)
./deployed/deploy.sh

# Setup git auto-deploy hook
./deployed/setup-git-hook.sh

# Manual restart
./start.sh
```

## Architecture & Key Concepts

### Multi-Project System
The system supports three medical education platforms:
- **GS** (Gynecology School) - gynecology.school
- **PS** (Pediatrics School) - pediatrics.school
- **TS** (Therapy School) - therapy.school

Each project has separate Bitrix CMS API endpoints and content customization (topics, style, audience).

### Backend Structure
```
backend/
├── main.py                 # FastAPI app entry, lifespan management
├── core/
│   ├── config.py          # Settings (DB, API keys, CORS, projects)
│   └── env_validator.py   # Environment validation
├── api/                   # API endpoints (routers)
│   ├── auth.py           # Login/logout with HttpOnly cookies
│   ├── users.py          # User management (admin/staff/analyst roles)
│   ├── news.py           # News parsing, articles CRUD
│   ├── news_generation.py # AI article generation
│   ├── image_generation.py # Yandex Cloud image generation
│   ├── telegram_posts.py  # Telegram publishing
│   ├── url_articles.py    # Parse & generate from URL
│   └── settings.py        # App settings management
├── services/             # Business logic
│   ├── *_parser.py       # News source parsers (medvestnik, ria, etc.)
│   ├── ai_service.py     # OpenAI GPT-4 integration
│   ├── ai_provider.py    # AI provider abstraction
│   ├── auth_service.py   # User authentication
│   ├── settings_service.py # Settings CRUD
│   └── scheduler.py      # Background tasks (disabled, uses cron)
├── database/
│   ├── models.py         # SQLModel ORM models
│   ├── schemas.py        # Pydantic schemas
│   ├── service.py        # Database operations
│   └── connection.py     # DB connection setup
└── middleware/
    └── rate_limiter.py   # Rate limiting per endpoint
```

### Frontend Structure
```
frontend/
├── pages/
│   ├── index.js          # Main dashboard (news parsing)
│   ├── published.js      # Generated articles management
│   ├── login.js          # Authentication
│   ├── settings.js       # App settings
│   ├── expenses.js       # AI cost tracking
│   └── monitoring.js     # News monitoring (main page)
├── components/
│   ├── ArticleEditor.js  # Rich text editor (Quill)
│   ├── NewsCard.js       # News article display
│   ├── BitrixProjectSelector.js # Multi-project switcher
│   └── ...
├── contexts/
│   └── AuthContext.js    # Authentication state
└── utils/
    └── api.js            # Axios API client
```

### Authentication Flow
1. **Login**: POST `/api/auth/login` → returns JWT in HttpOnly cookie + user data
2. **Auth Check**: All protected routes verify JWT cookie via `get_current_user` dependency
3. **CORS**: Production uses `https://admin.news.rmevent.ru` (nginx proxy), allows credentials
4. **CSRF**: Token verification for state-changing operations
5. **Roles**: `admin` (full access), `staff` (content management), `analyst` (read-only)

### News Workflow
1. **Parsing**: Manual trigger or daily auto-parse at 02:00 MSK → saves to `articles` table
2. **AI Generation**: Select article → AI rewrites for target project → saves to `generated_articles` table
3. **Editing**: Rich text editor with draft auto-save
4. **Publishing**:
   - **Bitrix CMS**: Sends to project-specific API endpoint
   - **Telegram**: Posts to configured channel
5. **Monitoring**: Track AI expenses (OpenAI, Yandex), system metrics

### Database Models (Key Tables)
- `articles` - Parsed news articles from sources
- `generated_articles` - AI-generated content with project associations
- `users` - User accounts with roles
- `source_stats` - Parsing statistics per source
- `parse_sessions` - Track parsing operations
- `settings` - App configuration (key-value store)
- `ai_expenses` - Track OpenAI/Yandex API costs

### Configuration Management
- **Backend**: `.env` file (DATABASE_URL, API keys, JWT_SECRET_KEY, etc.)
- **Frontend**: `.env.production` (NEXT_PUBLIC_API_URL, BACKEND_API_URL)
- **Docker**: `docker-compose.yml` maps `.env` to container environment
- **Nginx**: `nginx-server.conf` handles SSL termination and proxying

### Important Conventions
1. **Always use Moscow timezone** (`ZoneInfo("Europe/Moscow")`) for scheduling
2. **HttpOnly cookies** for JWT tokens - never expose to JavaScript
3. **CORS** strict in production - only allow `admin.news.rmevent.ru`
4. **Rate limiting** enabled per endpoint (auth, parsing, generation, admin)
5. **Database migrations** required for any model changes - use Alembic
6. **Daily parsing** runs at 02:00 MSK via internal scheduler (not cron)
7. **Publication scheduling** uses external cron calling `scripts/publish_scheduled_news.py`

### Security Notes
- Never commit `.env` files with real credentials
- Default admin password: `Adm1n-tr0ng_P@ssw0rd2024!` (change in production!)
- JWT secret must be strong and kept secret
- All API keys (OpenAI, Yandex, Telegram) in environment variables only

### Common Debugging
```bash
# Check auth issues
docker logs medical-news-backend | grep -i auth

# Check CORS issues
docker logs medical-news-backend | grep CORS

# Check database connection
docker exec medical-news-backend psql -h 172.20.0.1 -U postgres -d news_aggregator

# Health checks
curl http://localhost:8000/health
curl https://admin.news.rmevent.ru/api/health

# View nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Testing Approach
- **Backend**: pytest for unit/integration tests
- **Frontend**: npm test (Jest/React Testing Library)
- Always test auth flows, CORS, and multi-project logic

## Code Ownership (from CODEOWNERS)
- **Backend**: @backend-team
- **Frontend**: @frontend-team
- **Infrastructure**: @devops-team
- **Database migrations**: @db-team @backend-team
- **Security files**: @security-team @backend-team
- **Documentation**: @tech-writers @team-leads
