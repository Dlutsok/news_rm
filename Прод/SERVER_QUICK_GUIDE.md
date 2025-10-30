# Server Quick Guide - Medical News System

## 🔗 Основные ссылки
- **Сайт:** https://admin.news.rmevent.ru
- **Сервер:** 176.124.219.201
- **SSH:** `ssh root@176.124.219.201` (пароль: `xQ6P+4_3mmJBcs`)

---

## ⚡ Быстрые команды

### Подключение к серверу
```bash
ssh root@176.124.219.201
cd /opt/medical-news/deployed
```

### Проверка статуса
```bash
docker ps                              # Статус всех контейнеров
docker compose ps                      # Статус через compose
curl http://localhost:8000/health      # Здоровье backend
curl https://admin.news.rmevent.ru     # Проверка сайта
```

### Перезапуск сервисов
```bash
# Один сервис
docker compose restart backend
docker compose restart frontend
docker compose restart nginx

# Все сервисы
docker compose down && docker compose up -d
```

### Логи
```bash
# Просмотр логов
docker logs -f medical-news-backend    # Backend (follow)
docker logs -f medical-news-frontend   # Frontend
docker logs -f medical-news-nginx      # Nginx

# Последние 100 строк
docker logs medical-news-backend --tail 100

# Cleanup лог
tail -f /var/log/medical-news-cleanup.log

# Publication лог
tail -f /root/logs/publication_cron.log
```

---

## 🚀 Деплой обновлений

### Локально (на Mac)
```bash
cd "/Users/dan/Documents/RM Service/SEO NEW 5"

# Коммит изменений
git add .
git commit -m "описание изменений"
git push origin main

# Ждем GitHub Actions (~5-10 минут)
# Проверить: https://github.com/Dlutsok/news_rm/actions
```

### На сервере
```bash
ssh root@176.124.219.201
cd /opt/medical-news/deployed

# Подтянуть новые образы
docker compose pull

# Перезапустить контейнеры
docker compose up -d

# Проверить статус
docker ps
```

---

## 🔧 Частые проблемы и решения

### 1. Изображения не загружаются (404)
```bash
# Проверить volume
ls /opt/medical-news/deployed/storage/images/

# Проверить backend
curl http://localhost:8000/images/FILENAME.jpeg

# Проверить nginx
docker logs medical-news-nginx --tail 50 | grep images

# Решение: перезапустить nginx
docker compose restart nginx
```

### 2. Backend не отвечает
```bash
# Проверить логи
docker logs medical-news-backend --tail 100

# Проверить БД подключение
docker exec medical-news-backend env | grep DATABASE

# Перезапустить
docker compose restart backend
```

### 3. Сайт недоступен (502/503)
```bash
# Проверить все контейнеры
docker ps

# Проверить nginx
docker logs medical-news-nginx --tail 50

# Полный перезапуск
docker compose down
docker compose up -d
```

### 4. Закончилось место на диске
```bash
# Проверить место
df -h

# Ручная очистка
bash /opt/medical-news/deployed/daily-cleanup.sh

# Удалить старые образы
docker image prune -a
```

---

## 📅 Автоматические задачи

### Cron Jobs
```bash
# Просмотр
crontab -l

# Редактирование
crontab -e
```

**Текущие задачи:**
- `* * * * *` - Публикация статей (каждую минуту)
- `0 3 * * *` - Cleanup системы (каждый день в 03:00)

**Парсинг новостей:**
- Встроен в backend, запускается в 02:00 МСК

---

## 🗂️ Структура директорий

```
/opt/medical-news/deployed/
├── docker-compose.yml          # Docker конфигурация
├── .env                        # Environment variables
├── daily-cleanup.sh            # Скрипт очистки
├── storage/
│   └── images/                 # 🖼️ Сохраненные изображения (297 MB)
├── logs/                       # Backend логи
├── nginx-logs/                 # Nginx логи
└── chat_history.db             # История чатов

/var/log/
└── medical-news-cleanup.log    # Лог cleanup скрипта

/root/
├── scripts/
│   └── cron_publish_news.sh    # Скрипт публикации
└── logs/
    └── publication_cron.log     # Лог публикаций
```

---

## 💾 Backup & Restore

### Backup изображений
```bash
# На сервере
cd /opt/medical-news/deployed
tar -czf images-backup-$(date +%Y%m%d).tar.gz storage/images/
```

### Backup БД (если нужно)
```bash
docker exec medical-news-backend pg_dump \
  -h 172.17.0.1 -U postgres -d news_aggregator \
  > backup-$(date +%Y%m%d).sql
```

---

## 🔐 Секретные ключи (храни в безопасности!)

**SSH:**
- Сервер: `176.124.219.201`
- Пользователь: `root`
- Пароль: `xQ6P+4_3mmJBcs`

**БД:**
- Host: `172.17.0.1:5432`
- User: `postgres`
- Password: `medical2024`
- Database: `news_aggregator`

**API Keys (на сервере в .env):**
- OpenAI API Key
- Yandex Cloud API Key
- Telegram Bot Token

---

## 📊 Мониторинг

### Ресурсы системы
```bash
# CPU/Memory
free -h
htop
docker stats

# Disk
df -h
du -sh /opt/medical-news/deployed/storage/images/

# Load
uptime
```

### Проверка работоспособности
```bash
# Backend health
curl http://localhost:8000/health

# Сайт
curl -I https://admin.news.rmevent.ru

# Изображение
curl -I https://admin.news.rmevent.ru/images/FILENAME.jpeg

# SSL
curl -I https://admin.news.rmevent.ru | grep -i ssl
```

---

## 🆘 Аварийные процедуры

### Полный перезапуск системы
```bash
ssh root@176.124.219.201
cd /opt/medical-news/deployed

# Остановить все
docker compose down

# Очистить (опционально)
docker system prune -f

# Запустить
docker compose up -d

# Проверить
docker ps
docker logs -f medical-news-backend
```

### Откат к предыдущей версии
```bash
# Посмотреть доступные образы
docker images | grep medical-news

# Указать конкретный tag в .env
echo "TAG=previous-version" >> .env

# Перезапустить
docker compose down
docker compose up -d
```

---

## 📞 Контакты для поддержки

- **GitHub:** https://github.com/Dlutsok/news_rm
- **Issues:** https://github.com/Dlutsok/news_rm/issues
- **Документация:** `/docs/` в репозитории

---

**Последнее обновление:** 30 октября 2025
**Версия:** 1.0
