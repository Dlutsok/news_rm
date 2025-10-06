# Руководство по развертыванию

## Обзор

Система медицинских новостей состоит из двух основных компонентов:
- **Backend**: FastAPI приложение на Python
- **Frontend**: Next.js приложение на React

Поддерживаются различные среды развертывания: Development, Staging, Production.

## Требования системы

### Минимальные требования
- **CPU**: 2 ядра
- **RAM**: 4 GB
- **Диск**: 20 GB SSD
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+

### Рекомендуемые требования (Production)
- **CPU**: 4 ядра
- **RAM**: 8 GB
- **Диск**: 50 GB SSD
- **ОС**: Ubuntu 22.04 LTS

### Программное обеспечение
- **Python**: 3.11+
- **Node.js**: 18.0+
- **PostgreSQL**: 14+ (для production)
- **Nginx**: 1.20+ (для production)
- **Docker**: 20.10+ (опционально)
- **Git**: 2.30+

## Подготовка сервера

### 1. Обновление системы
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 2. Установка зависимостей
```bash
# Ubuntu/Debian
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm postgresql postgresql-contrib nginx git curl

# CentOS/RHEL
sudo yum install -y python311 python3-pip nodejs npm postgresql postgresql-server nginx git curl
```

### 3. Настройка пользователя
```bash
# Создание пользователя для приложения
sudo useradd -m -s /bin/bash medapp
sudo usermod -aG sudo medapp

# Переключение на пользователя
sudo su - medapp
```

### 4. Настройка PostgreSQL (Production)
```bash
# Инициализация БД (если нужно)
sudo postgresql-setup --initdb

# Запуск сервиса
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Создание пользователя и базы
sudo -u postgres createuser medapp_user
sudo -u postgres createdb medapp_db -O medapp_user
sudo -u postgres psql -c "ALTER USER medapp_user PASSWORD 'secure_password';"
```

## Development развертывание

### 1. Клонирование репозитория
```bash
git clone https://github.com/yourorg/medical-news-system.git
cd medical-news-system
```

### 2. Настройка Backend
```bash
cd backend

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Копирование конфигурации
cp .env.example .env

# Редактирование конфигурации
nano .env
```

**Настройка .env для development:**
```env
# Основные настройки
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your_secret_key_here

# База данных
DATABASE_URL=sqlite:///./development.db

# AI сервисы
OPENAI_API_KEY=your_openai_key
AI_PROVIDER=openai

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# JWT
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Bitrix (опционально)
BITRIX_API_URL=
BITRIX_API_TOKEN=
```

### 3. Инициализация Backend
```bash
# Создание таблиц БД
python -c "from database.connection import init_database; init_database()"

# Запуск сервера
python main.py
```

### 4. Настройка Frontend
```bash
# Новый терминал
cd frontend

# Установка зависимостей
npm install

# Копирование конфигурации
cp .env.local.example .env.local

# Редактирование конфигурации
nano .env.local
```

**Настройка .env.local:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

### 5. Запуск Frontend
```bash
npm run dev
```

### 6. Проверка
Откройте браузер и перейдите по адресу:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Документация API: http://localhost:8000/docs

## Production развертывание

### 1. Подготовка кода
```bash
# Клонирование в production директорию
sudo mkdir -p /opt/medapp
sudo chown medapp:medapp /opt/medapp
cd /opt/medapp

git clone https://github.com/yourorg/medical-news-system.git .
git checkout main
```

### 2. Настройка Backend
```bash
cd /opt/medapp/backend

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка конфигурации
sudo cp .env.production.example .env
sudo chown medapp:medapp .env
nano .env
```

**Настройка .env для production:**
```env
# Основные настройки
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=very_secure_secret_key_here

# База данных
DATABASE_URL=postgresql://medapp_user:secure_password@localhost/medapp_db

# AI сервисы
OPENAI_API_KEY=your_production_openai_key
AI_PROVIDER=openai

# CORS
CORS_ORIGINS=["https://yourdomain.com"]

# JWT
JWT_SECRET_KEY=very_secure_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Bitrix
BITRIX_API_URL=https://your-bitrix.com/api
BITRIX_API_TOKEN=your_production_token

# Логирование
LOG_LEVEL=INFO
LOG_FILE=/var/log/medapp/backend.log
```

### 3. Настройка базы данных
```bash
# Создание директорий
sudo mkdir -p /var/log/medapp
sudo chown medapp:medapp /var/log/medapp

# Инициализация БД
source venv/bin/activate
python -c "from database.connection import init_database; init_database()"
```

### 4. Создание systemd сервиса для Backend
```bash
sudo nano /etc/systemd/system/medapp-backend.service
```

```ini
[Unit]
Description=Medical News Backend
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=medapp
Group=medapp
WorkingDirectory=/opt/medapp/backend
Environment=PATH=/opt/medapp/backend/venv/bin
ExecStart=/opt/medapp/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=3

# Безопасность
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/opt/medapp /var/log/medapp
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 5. Настройка Frontend
```bash
cd /opt/medapp/frontend

# Установка зависимостей
npm ci --only=production

# Настройка конфигурации
cp .env.production.example .env.production
nano .env.production
```

**Настройка .env.production:**
```env
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
NEXT_PUBLIC_ENVIRONMENT=production
```

### 6. Сборка Frontend
```bash
# Сборка приложения
npm run build

# Проверка сборки
npm start
```

### 7. Создание systemd сервиса для Frontend
```bash
sudo nano /etc/systemd/system/medapp-frontend.service
```

```ini
[Unit]
Description=Medical News Frontend
After=network.target

[Service]
Type=simple
User=medapp
Group=medapp
WorkingDirectory=/opt/medapp/frontend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=3

# Переменные окружения
Environment=NODE_ENV=production
Environment=PORT=3000

# Безопасность
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/opt/medapp
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 8. Настройка Nginx
```bash
sudo nano /etc/nginx/sites-available/medapp
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL сертификаты
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Безопасность
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Логирование
    access_log /var/log/nginx/medapp_access.log;
    error_log /var/log/nginx/medapp_error.log;

    # Главное приложение
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        
        # Увеличенные таймауты для долгих операций
        location /api/news/parse {
            proxy_pass http://127.0.0.1:8000/api/news/parse;
            proxy_read_timeout 600;
            proxy_connect_timeout 600;
            proxy_send_timeout 600;
        }
    }

    # Статические файлы
    location /_next/static/ {
        proxy_pass http://127.0.0.1:3000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Изображения
    location /api/images/storage/ {
        proxy_pass http://127.0.0.1:8000/api/images/storage/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
```

### 9. Активация конфигурации
```bash
# Активация сайта
sudo ln -s /etc/nginx/sites-available/medapp /etc/nginx/sites-enabled/

# Удаление дефолтного сайта
sudo rm /etc/nginx/sites-enabled/default

# Проверка конфигурации
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx
```

### 10. Настройка SSL (Let's Encrypt)
```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Автообновление сертификата
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### 11. Запуск сервисов
```bash
# Активация и запуск сервисов
sudo systemctl enable medapp-backend
sudo systemctl enable medapp-frontend
sudo systemctl enable nginx
sudo systemctl enable postgresql

sudo systemctl start medapp-backend
sudo systemctl start medapp-frontend
sudo systemctl start nginx

# Проверка статуса
sudo systemctl status medapp-backend
sudo systemctl status medapp-frontend
sudo systemctl status nginx
```

## Docker развертывание

### 1. Подготовка Dockerfile для Backend
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание пользователя
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Подготовка Dockerfile для Frontend
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Установка зависимостей
COPY package*.json ./
RUN npm ci --only=production

# Сборка приложения
COPY . .
RUN npm run build

# Production образ
FROM node:18-alpine AS runner

WORKDIR /app

# Создание пользователя
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Копирование файлов
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
```

### 3. Docker Compose конфигурация
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: medapp_db
      POSTGRES_USER: medapp_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://medapp_user:secure_password@postgres/medapp_db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    restart: unless-stopped
    volumes:
      - ./backend/storage:/app/storage

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

### 4. Запуск Docker Compose
```bash
# Создание .env файла
cp .env.example .env
nano .env

# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка сервисов
docker-compose down
```

## Мониторинг и обслуживание

### 1. Проверка состояния сервисов
```bash
# Статус systemd сервисов
sudo systemctl status medapp-backend
sudo systemctl status medapp-frontend
sudo systemctl status nginx
sudo systemctl status postgresql

# Просмотр логов
sudo journalctl -u medapp-backend -f
sudo journalctl -u medapp-frontend -f

# Логи Nginx
sudo tail -f /var/log/nginx/medapp_access.log
sudo tail -f /var/log/nginx/medapp_error.log
```

### 2. Обновление приложения
```bash
# Переход в директорию проекта
cd /opt/medapp

# Создание резервной копии
sudo cp -r /opt/medapp /opt/medapp_backup_$(date +%Y%m%d_%H%M%S)

# Получение обновлений
git fetch origin
git checkout main
git pull origin main

# Обновление Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Применение миграций БД (если есть)
# python migrate.py

# Перезапуск Backend
sudo systemctl restart medapp-backend

# Обновление Frontend
cd ../frontend
npm ci --only=production
npm run build

# Перезапуск Frontend
sudo systemctl restart medapp-frontend

# Проверка статуса
sudo systemctl status medapp-backend
sudo systemctl status medapp-frontend
```

### 3. Резервное копирование
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/medapp"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории бэкапов
mkdir -p $BACKUP_DIR

# Бэкап базы данных
pg_dump -h localhost -U medapp_user medapp_db > $BACKUP_DIR/db_backup_$DATE.sql

# Бэкап файлов приложения
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz /opt/medapp

# Бэкап изображений
tar -czf $BACKUP_DIR/images_backup_$DATE.tar.gz /opt/medapp/backend/storage

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*backup*" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### 4. Настройка cron для автоматических бэкапов
```bash
# Редактирование crontab
crontab -e

# Добавление задачи (каждый день в 3:00)
0 3 * * * /opt/medapp/scripts/backup.sh >> /var/log/medapp/backup.log 2>&1
```

## Устранение неполадок

### Общие проблемы

1. **Backend не запускается**
   - Проверьте логи: `sudo journalctl -u medapp-backend -n 50`
   - Проверьте .env конфигурацию
   - Убедитесь что PostgreSQL запущен
   - Проверьте доступность порта 8000

2. **Frontend не запускается**
   - Проверьте логи: `sudo journalctl -u medapp-frontend -n 50`
   - Убедитесь что сборка прошла успешно
   - Проверьте доступность порта 3000
   - Проверьте подключение к Backend API

3. **Nginx ошибки**
   - Проверьте конфигурацию: `sudo nginx -t`
   - Проверьте логи: `sudo tail -f /var/log/nginx/error.log`
   - Убедитесь что сервисы доступны на указанных портах

4. **База данных недоступна**
   - Проверьте статус PostgreSQL: `sudo systemctl status postgresql`
   - Проверьте подключение: `psql -h localhost -U medapp_user -d medapp_db`
   - Проверьте настройки в .env файле

### Команды диагностики
```bash
# Проверка портов
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :3000
sudo netstat -tlnp | grep :5432

# Проверка процессов
ps aux | grep uvicorn
ps aux | grep node
ps aux | grep nginx

# Проверка дискового пространства
df -h

# Проверка памяти
free -h

# Проверка логов
sudo journalctl -xe
```

## Безопасность

### 1. Настройка файрвола
```bash
# UFW (Ubuntu)
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Проверка статуса
sudo ufw status
```

### 2. Обновления безопасности
```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

### 3. Мониторинг
```bash
# Установка fail2ban
sudo apt install fail2ban

# Конфигурация для Nginx
sudo nano /etc/fail2ban/jail.local
```

```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-noscript]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 6
```

Это руководство покрывает основные сценарии развертывания системы медицинских новостей от development до production окружения.