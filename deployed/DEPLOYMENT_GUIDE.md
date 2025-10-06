# Production Deployment Guide

Полное руководство по деплою Medical News Automation на продакшн сервер.

## Содержание
1. [Требования](#требования)
2. [Первоначальная настройка](#первоначальная-настройка)
3. [Деплой](#деплой)
4. [Проверка](#проверка)
5. [Откат изменений](#откат-изменений)
6. [Troubleshooting](#troubleshooting)

---

## Требования

### Сервер
- Ubuntu 20.04+ или аналог
- Docker 20.10+
- Docker Compose 2.0+
- Nginx с SSL (Let's Encrypt)
- PostgreSQL 14+
- Минимум 4GB RAM
- Минимум 20GB свободного места

### Доступы
- SSH доступ к серверу (176.124.219.201)
- Доступ к БД PostgreSQL (172.20.0.1:5432)
- Доступ к домену (admin.news.rmevent.ru)

---

## Первоначальная настройка

### 1. Подготовка сервера

```bash
# Подключение к серверу
ssh user@176.124.219.201

# Создание директории проекта
sudo mkdir -p /var/www/medical-news
sudo chown $USER:$USER /var/www/medical-news
cd /var/www/medical-news

# Клонирование проекта
git clone <repository-url> .
```

### 2. Настройка PostgreSQL

```bash
# Проверка что БД доступна
PGPASSWORD=YOUR_DB_PASSWORD psql -h 172.20.0.1 -U postgres -d news_aggregator -c "SELECT 1;"

# Если БД не существует, создать
PGPASSWORD=YOUR_DB_PASSWORD psql -h 172.20.0.1 -U postgres -c "CREATE DATABASE news_aggregator;"
```

### 3. Копирование конфигов

```bash
# Скопировать файлы из deployed/
cp deployed/.env .env
cp deployed/nginx.conf /etc/nginx/sites-available/medical-news

# Активировать nginx конфиг
sudo ln -s /etc/nginx/sites-available/medical-news /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. SSL сертификаты

```bash
# Если еще нет сертификата
sudo certbot --nginx -d admin.news.rmevent.ru

# Проверка автообновления
sudo certbot renew --dry-run
```

---

## Деплой

### Автоматический деплой (рекомендуется)

```bash
cd /var/www/medical-news

# Запустить скрипт деплоя
./deployed/deploy.sh
```

Скрипт автоматически:
1. ✅ Проверит конфигурацию
2. 💾 Создаст бэкап БД
3. 🛑 Остановит старые контейнеры
4. 🏗️ Соберет новые образы
5. 🚀 Запустит контейнеры
6. ⏳ Дождется готовности
7. 🔄 Перезагрузит nginx

### Ручной деплой

```bash
# 1. Бэкап БД
mkdir -p backups
PGPASSWORD=YOUR_DB_PASSWORD pg_dump -h 172.20.0.1 -U postgres -d news_aggregator > backups/backup_$(date +%Y%m%d).sql

# 2. Остановка контейнеров
docker-compose down

# 3. Сборка образов
docker-compose build --no-cache

# 4. Запуск
docker-compose up -d

# 5. Проверка логов
docker logs medical-news-backend -f
docker logs medical-news-frontend -f

# 6. Перезагрузка nginx
sudo nginx -t && sudo systemctl reload nginx
```

---

## Проверка

### 1. Проверка контейнеров

```bash
# Статус контейнеров
docker ps

# Должны быть запущены:
# - medical-news-backend   (healthy)
# - medical-news-frontend  (healthy)
# - db-health-check        (exited)
```

### 2. Проверка endpoints

```bash
# Backend health
curl http://176.124.219.201:8001/health

# Frontend
curl http://176.124.219.201:3000

# HTTPS через nginx
curl https://admin.news.rmevent.ru

# API через nginx
curl https://admin.news.rmevent.ru/api/health
```

### 3. Проверка логов

```bash
# Backend логи
docker logs medical-news-backend --tail 100

# Frontend логи
docker logs medical-news-frontend --tail 100

# Nginx логи
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 4. Проверка авторизации

```bash
# Тест логина
curl -X POST https://admin.news.rmevent.ru/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Adm1n-tr0ng_P@ssw0rd2024!"}'

# Должен вернуть access_token
```

---

## Откат изменений

### Быстрый откат

```bash
# 1. Остановить новые контейнеры
docker-compose down

# 2. Восстановить из бэкапа БД (если нужно)
PGPASSWORD=YOUR_DB_PASSWORD psql -h 172.20.0.1 -U postgres -d news_aggregator < backups/backup_YYYYMMDD.sql

# 3. Запустить старую версию
git checkout <previous-commit>
docker-compose up -d
```

### Откат БД

```bash
# Список бэкапов
ls -lh backups/

# Восстановление
PGPASSWORD=YOUR_DB_PASSWORD psql -h 172.20.0.1 -U postgres -d news_aggregator < backups/backup_20241006.sql
```

---

## Troubleshooting

### Backend не запускается

**Проблема**: Контейнер medical-news-backend постоянно перезапускается

```bash
# Проверить логи
docker logs medical-news-backend --tail 200

# Частые причины:
# 1. БД недоступна
PGPASSWORD=YOUR_DB_PASSWORD psql -h 172.20.0.1 -U postgres -d news_aggregator -c "SELECT 1;"

# 2. Неправильный .env
docker exec medical-news-backend env | grep DATABASE_URL

# 3. Порт занят
sudo lsof -i :8001
```

### CORS ошибки

**Проблема**: Frontend получает CORS ошибки при запросах к API

```bash
# 1. Проверить DEBUG в .env
docker exec medical-news-backend env | grep DEBUG
# Должно быть: DEBUG=False

# 2. Проверить CORS_ORIGINS_PRODUCTION
docker exec medical-news-backend env | grep CORS_ORIGINS_PRODUCTION
# Должно включать: https://admin.news.rmevent.ru

# 3. Перезапустить backend
docker-compose restart backend
```

### 502 Bad Gateway

**Проблема**: Nginx возвращает 502 ошибку

```bash
# 1. Проверить что контейнеры запущены
docker ps | grep medical-news

# 2. Проверить nginx конфиг
sudo nginx -t

# 3. Проверить доступность backend
curl http://176.124.219.201:8001/health

# 4. Проверить nginx логи
sudo tail -f /var/log/nginx/error.log
```

### База данных недоступна

**Проблема**: Backend не может подключиться к БД

```bash
# 1. Проверить что PostgreSQL запущен
sudo systemctl status postgresql

# 2. Проверить доступность с хоста
PGPASSWORD=YOUR_DB_PASSWORD psql -h 172.20.0.1 -U postgres -d news_aggregator -c "SELECT version();"

# 3. Проверить настройки pg_hba.conf
sudo cat /etc/postgresql/*/main/pg_hba.conf | grep 172.20.0.0

# Должна быть строка:
# host    all    all    172.20.0.0/16    md5

# 4. Перезапустить PostgreSQL
sudo systemctl restart postgresql
```

### Авторизация не работает

**Проблема**: Логин успешный, но /api/auth/me возвращает 403

```bash
# 1. Проверить JWT_SECRET_KEY одинаковый везде
docker exec medical-news-backend env | grep JWT_SECRET_KEY

# 2. Проверить логи авторизации
docker logs medical-news-backend | grep -i "auth\|token"

# 3. Проверить что токен передается
# Открыть DevTools → Network → Headers → Authorization
```

---

## Мониторинг

### Полезные команды

```bash
# Статус всех сервисов
docker-compose ps

# Использование ресурсов
docker stats

# Размер образов
docker images | grep medical-news

# Очистка неиспользуемых образов
docker system prune -a

# Логи в реальном времени
docker-compose logs -f

# Перезапуск отдельного сервиса
docker-compose restart backend
```

### Автоматический мониторинг

Добавить в crontab для проверки работоспособности:

```bash
# Открыть crontab
crontab -e

# Добавить проверку каждые 5 минут
*/5 * * * * curl -f http://localhost:8001/health || systemctl restart docker
```

---

## Контакты поддержки

- Документация проекта: `/docs/`
- Backend API: `https://admin.news.rmevent.ru/api/docs`
- Логи проекта: `/var/www/medical-news/logs/`
