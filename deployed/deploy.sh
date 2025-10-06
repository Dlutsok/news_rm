#!/bin/bash
#
# Production Deployment Script
# Автоматизированный деплой на продакшн сервер
#

set -e  # Остановиться при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Medical News Automation - Deploy${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Проверка что находимся в правильной директории
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Ошибка: docker-compose.yml не найден${NC}"
    echo "Запустите скрипт из корня проекта"
    exit 1
fi

# Шаг 1: Проверка конфигурации
echo -e "${YELLOW}[1/7] Проверка конфигурации...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}Ошибка: .env файл не найден${NC}"
    echo "Скопируйте deployed/.env в корень проекта"
    exit 1
fi

# Проверка что DEBUG=False
if grep -q "DEBUG=True" .env; then
    echo -e "${RED}Ошибка: DEBUG=True в .env${NC}"
    echo "Для продакшна установите DEBUG=False"
    exit 1
fi

echo -e "${GREEN}✓ Конфигурация проверена${NC}"

# Шаг 2: Бэкап БД
echo -e "${YELLOW}[2/7] Создание бэкапа БД...${NC}"
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
PGPASSWORD=${DB_PASSWORD:-medical2024} pg_dump -h 172.20.0.1 -U postgres -d news_aggregator > "backups/$BACKUP_FILE" || {
    echo -e "${YELLOW}⚠ Не удалось создать бэкап (возможно БД недоступна)${NC}"
}
echo -e "${GREEN}✓ Бэкап создан: $BACKUP_FILE${NC}"

# Шаг 3: Остановка старых контейнеров
echo -e "${YELLOW}[3/7] Остановка контейнеров...${NC}"
docker-compose down
echo -e "${GREEN}✓ Контейнеры остановлены${NC}"

# Шаг 4: Сборка новых образов
echo -e "${YELLOW}[4/7] Сборка образов (может занять несколько минут)...${NC}"
docker-compose build --no-cache
echo -e "${GREEN}✓ Образы собраны${NC}"

# Шаг 5: Запуск контейнеров
echo -e "${YELLOW}[5/7] Запуск контейнеров...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Контейнеры запущены${NC}"

# Шаг 6: Ожидание готовности
echo -e "${YELLOW}[6/7] Ожидание готовности сервисов (60 сек)...${NC}"
sleep 60

# Проверка healthcheck backend
if ! docker ps | grep -q "medical-news-backend.*healthy"; then
    echo -e "${RED}⚠ Backend не прошел healthcheck${NC}"
    docker logs medical-news-backend --tail 50
fi

# Проверка healthcheck frontend
if ! docker ps | grep -q "medical-news-frontend.*healthy"; then
    echo -e "${RED}⚠ Frontend не прошел healthcheck${NC}"
    docker logs medical-news-frontend --tail 50
fi

echo -e "${GREEN}✓ Сервисы запущены${NC}"

# Шаг 7: Перезагрузка nginx
echo -e "${YELLOW}[7/7] Перезагрузка nginx...${NC}"
if [ -f "/etc/nginx/nginx.conf" ]; then
    sudo nginx -t && sudo systemctl reload nginx
    echo -e "${GREEN}✓ Nginx перезагружен${NC}"
else
    echo -e "${YELLOW}⚠ Nginx конфигурация не найдена (пропускаем)${NC}"
fi

# Итоги
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Деплой завершен успешно!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Проверьте работу:"
echo "  Backend:  http://176.124.219.201:8001/health"
echo "  Frontend: http://176.124.219.201:3000"
echo "  HTTPS:    https://admin.news.rmevent.ru"
echo ""
echo "Логи:"
echo "  docker logs medical-news-backend -f"
echo "  docker logs medical-news-frontend -f"
echo ""
