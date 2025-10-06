# Production Deployment - Продакшн деплой

Эта папка содержит **все конфигурационные файлы и скрипты для продакшн сервера**.

> **Полная документация**: См. [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) для детальных инструкций

## Структура

```
deployed/
├── .env                    # Backend environment для продакшна (НЕ коммитить!)
├── frontend.env            # Frontend environment для продакшна (НЕ коммитить!)
├── docker-compose.yml      # Docker compose для продакшна
├── nginx.conf              # Nginx конфигурация
├── deploy.sh               # Скрипт ручного деплоя
├── git-deploy.sh           # Скрипт автодеплоя через Git
├── setup-git-hook.sh       # Установка автодеплоя (Git Hook/Cron/Webhook)
├── DEPLOYMENT_GUIDE.md     # Полное руководство по деплою
├── CI-CD-GUIDE.md          # Руководство по автодеплою
└── README.md               # Этот файл
```

## Быстрый деплой

### Вариант 1: Ручной деплой
```bash
cd /var/www/medical-news
./deployed/deploy.sh
```

### Вариант 2: Автодеплой через Git
```bash
# Установить автодеплой (один раз)
cd /var/www/medical-news
./deployed/setup-git-hook.sh

# Теперь при git push изменения автоматически деплоятся!
```

См. [`CI-CD-GUIDE.md`](CI-CD-GUIDE.md) для настройки автоматического деплоя.

## Файлы

### `.env` - Backend окружение
- `DEBUG=False` - продакшн режим
- `DATABASE_URL` - продакшн БД с правильным паролем
- `CORS_ORIGINS_PRODUCTION` - только HTTPS домены
- Все API ключи и секреты

### `frontend.env` - Frontend окружение
- `NEXT_PUBLIC_API_URL=https://admin.news.rmevent.ru`
- Все запросы идут через nginx

### `docker-compose.yml` - Docker конфигурация
- Backend на порту 8001
- Frontend на порту 3000
- Правильные CORS настройки
- Healthchecks для всех сервисов

### `nginx.conf` - Nginx конфигурация
- HTTPS редирект
- `/api` → backend:8001
- `/` → frontend:3000
- SSL сертификаты Let's Encrypt

## Важно

⚠️ **НЕ коммитить в git!**

Файлы в этой папке содержат чувствительные данные (пароли, API ключи).
Добавьте в `.gitignore`:

```
deployed/.env
deployed/frontend.env
```

## Переменные окружения

### Backend (.env)
```bash
DEBUG=False                                    # Продакшн режим
DATABASE_URL=postgresql://...                  # Продакшн БД
JWT_SECRET_KEY=...                            # Одинаковый с dev
CORS_ORIGINS_PRODUCTION=https://...           # Только HTTPS
RATE_LIMITING_ENABLED=true                    # Включен rate limiting
```

### Frontend (frontend.env)
```bash
NEXT_PUBLIC_API_URL=https://admin.news.rmevent.ru
BACKEND_API_URL=https://admin.news.rmevent.ru
```

## Troubleshooting

### CORS ошибки
- Проверьте `CORS_ORIGINS_PRODUCTION` в `.env`
- Убедитесь что `DEBUG=False`
- Перезапустите backend контейнер

### 404 на /api
- Проверьте nginx.conf - должна быть секция `location /api`
- Перезагрузите nginx: `sudo systemctl reload nginx`
- Проверьте логи: `sudo tail -f /var/log/nginx/error.log`

### Авторизация не работает
- JWT_SECRET_KEY должен быть одинаковым с dev
- Проверьте что токены сохраняются в localStorage
- Проверьте логи backend: `docker logs medical-news-backend`

## Checklist перед деплоем

- [ ] Проверили `.env` - все ключи заполнены
- [ ] `DEBUG=False` в `.env`
- [ ] CORS настроен правильно
- [ ] SSL сертификаты обновлены
- [ ] Бэкап БД создан
- [ ] Docker контейнеры пересобраны
- [ ] Nginx перезагружен
- [ ] Тесты пройдены на стейджинге
