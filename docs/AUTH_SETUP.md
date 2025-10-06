# Настройка аутентификации для локального и продакшн окружения

## Обзор проблемы

Система использует JWT-токены для аутентификации. Токены создаются при логине и отправляются во frontend, который сохраняет их в `localStorage` и использует в заголовке `Authorization: Bearer <token>`.

## Архитектура

### Backend (FastAPI)
- **Эндпоинт логина**: `POST /api/auth/login`
  - Принимает username и password
  - Возвращает `{access_token, token_type}`
  - Токен создаётся с помощью JWT_SECRET_KEY

- **Эндпоинт информации о пользователе**: `GET /api/auth/me`
  - Требует заголовок: `Authorization: Bearer <token>`
  - Возвращает данные пользователя

- **Зависимости**: `get_current_user()` в `api/dependencies.py`
  - Извлекает токен из заголовка Authorization
  - Верифицирует токен используя JWT_SECRET_KEY
  - Загружает пользователя из БД

### Frontend (Next.js)
- **API клиент**: `utils/api.js`
  - Хранит токен в `localStorage`
  - Добавляет заголовок `Authorization: Bearer <token>` ко всем запросам

- **Auth контекст**: `contexts/AuthContext.js`
  - Управляет состоянием аутентификации
  - Вызывает `login()` и `getCurrentUser()`

## Настройка для локального окружения

### Backend (.env)
```bash
# Используется корневой .env файл
DEBUG=True
RELOAD=False

# CORS для локальной разработки
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# JWT ключи (должны быть одинаковыми для всех окружений одного проекта)
JWT_SECRET_KEY=dWiwTuG1vHPThqTiJhq-rfk691-L1tVDzCaJS_wvm6uwCYFTn2LlQPHnh7UkPS3oXEWpNh4Ik6HknwJGvmBUFw
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=12

# База данных
DATABASE_URL=postgresql://postgres:password@localhost:5432/news_aggregator

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Adm1n-tr0ng_P@ssw0rd2024!
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
API_BASE_URL=http://localhost:8000
CHAT_SERVICE_URL=http://localhost:8020
```

### Запуск локально
```bash
# Backend
cd backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev
```

## Настройка для продакшн окружения

### Backend (.env на продакшн сервере)
```bash
DEBUG=False
RELOAD=False

# CORS только для продакшн доменов
CORS_ORIGINS_PRODUCTION=https://admin.news.rusmedical.ru,https://admin.news.rmevent.ru

# JWT ключи (ВАЖНО: должны быть те же самые, что и в разработке)
JWT_SECRET_KEY=dWiwTuG1vHPThqTiJhq-rfk691-L1tVDzCaJS_wvm6uwCYFTn2LlQPHnh7UkPS3oXEWpNh4Ik6HknwJGvmBUFw
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=12

# Продакшн база данных
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/news_aggregator

# Admin credentials (ОБЯЗАТЕЛЬНО ИЗМЕНИТЬ!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=НАДЁЖНЫЙ_ПРОДАКШН_ПАРОЛЬ
```

### Frontend (.env.production)
```bash
NEXT_PUBLIC_API_URL=https://admin.news.rmevent.ru
API_BASE_URL=https://admin.news.rmevent.ru
CHAT_SERVICE_URL=https://admin.news.rmevent.ru
```

### Деплой на продакшн
```bash
# 1. Скопировать правильные .env файлы
cp .env.production.example .env  # и заполнить реальными значениями

# 2. Собрать и запустить через Docker
docker-compose up -d --build
```

## Важные моменты

### 1. JWT_SECRET_KEY должен быть одинаковым
- Если ключи разные в разработке и продакшене, токены не будут работать
- Для безопасности можно использовать разные ключи, но тогда пользователи должны заново логиниться при переносе между окружениями

### 2. CORS настройки
- Backend автоматически переключает CORS в зависимости от DEBUG:
  - `DEBUG=True`: используется `CORS_ORIGINS` (локальные домены)
  - `DEBUG=False`: используется `CORS_ORIGINS_PRODUCTION` (только продакшн домены)

### 3. Хранение токенов
- Токены хранятся в `localStorage` на клиенте
- Токены передаются в заголовке `Authorization: Bearer <token>`
- При 401 ошибке пользователь автоматически перенаправляется на /login

### 4. Логирование
- Добавлено детальное логирование в `api/dependencies.py`:
  - Верификация токена
  - Поиск пользователя
  - Успешная аутентификация
- Логи помогают отладить проблемы с авторизацией

## Диагностика проблем

### Проблема: 403 Forbidden после логина

**Причины:**
1. Токен не сохранился в localStorage
2. Токен не передаётся в заголовке Authorization
3. JWT_SECRET_KEY разный в backend и при создании токена
4. Токен истёк (проверить ACCESS_TOKEN_EXPIRE_HOURS)

**Решение:**
1. Проверить DevTools → Application → Local Storage → auth_token
2. Проверить DevTools → Network → Request Headers → Authorization
3. Проверить логи backend на наличие "Token verification failed"
4. Проверить что JWT_SECRET_KEY одинаковый в .env

### Проблема: CORS errors

**Причины:**
1. Frontend URL не добавлен в CORS_ORIGINS
2. Неправильное значение DEBUG в backend

**Решение:**
1. Добавить URL фронтенда в соответствующую переменную CORS
2. Убедиться что DEBUG=True для локальной разработки
3. Перезапустить backend после изменения .env

### Проблема: Неверные credentials при логине

**Причины:**
1. Пароль в БД не совпадает с паролем из .env
2. Пользователь не создан в БД

**Решение:**
```bash
# Обновить пароль админа в БД
cd backend
python3 -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
hashed = pwd_context.hash('Adm1n-tr0ng_P@ssw0rd2024!')
print(hashed)
"

# Скопировать хэш и выполнить SQL
PGPASSWORD=password psql -h localhost -U postgres -d news_aggregator -c "UPDATE users SET hashed_password = 'ВСТАВИТЬ_ХЭШ' WHERE username = 'admin';"
```

## Checklist для деплоя

- [ ] JWT_SECRET_KEY одинаковый в продакшн и разработке
- [ ] CORS_ORIGINS_PRODUCTION содержит продакшн домены
- [ ] DEBUG=False на продакшне
- [ ] ADMIN_PASSWORD изменён на надёжный
- [ ] DATABASE_URL указывает на продакшн БД
- [ ] Frontend .env.production содержит продакшн URL
- [ ] SSL сертификаты настроены для HTTPS
- [ ] Nginx проксирует запросы правильно
