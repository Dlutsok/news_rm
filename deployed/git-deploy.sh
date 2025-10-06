#!/bin/bash
#
# Git Auto-Deploy Script
# Автоматический деплой при git push
# Устанавливается как git hook на продакшн сервере
#

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Конфигурация
PROJECT_DIR="/var/www/medical-news"
BRANCH="main"
BACKUP_DIR="$PROJECT_DIR/backups"
LOG_FILE="$PROJECT_DIR/logs/deploy.log"

# Функция логирования
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Начало деплоя
log "========================================="
log "Starting Auto-Deploy from Git"
log "========================================="

# Переход в директорию проекта
cd "$PROJECT_DIR" || {
    error "Failed to change directory to $PROJECT_DIR"
    exit 1
}

# Шаг 1: Получение текущего коммита (для отката)
CURRENT_COMMIT=$(git rev-parse HEAD)
log "Current commit: $CURRENT_COMMIT"

# Шаг 2: Pull изменений из git
log "Pulling changes from git..."
git fetch origin "$BRANCH"

# Проверка есть ли новые изменения
if git diff --quiet HEAD origin/"$BRANCH"; then
    success "No changes detected, deployment skipped"
    exit 0
fi

NEW_COMMIT=$(git rev-parse origin/"$BRANCH")
log "New commit available: $NEW_COMMIT"

# Показать что изменилось
log "Changes to be deployed:"
git log --oneline "$CURRENT_COMMIT".."$NEW_COMMIT" | tee -a "$LOG_FILE"

# Шаг 3: Бэкап БД (перед применением изменений)
log "Creating database backup..."
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/auto_backup_$(date +%Y%m%d_%H%M%S).sql"

if PGPASSWORD=${DB_PASSWORD:-medical2024} pg_dump -h 172.20.0.1 -U postgres -d news_aggregator > "$BACKUP_FILE" 2>/dev/null; then
    success "Database backup created: $BACKUP_FILE"
else
    warning "Database backup failed (continuing deployment)"
fi

# Шаг 4: Проверка изменений в БД
log "Checking for database migrations..."
if git diff --name-only "$CURRENT_COMMIT" "$NEW_COMMIT" | grep -q "alembic/versions"; then
    warning "Database migrations detected!"
    DB_MIGRATION=true
else
    DB_MIGRATION=false
fi

# Шаг 5: Проверка изменений в зависимостях
REBUILD_BACKEND=false
REBUILD_FRONTEND=false

if git diff --name-only "$CURRENT_COMMIT" "$NEW_COMMIT" | grep -q "backend/requirements.txt"; then
    warning "Backend dependencies changed - full rebuild required"
    REBUILD_BACKEND=true
fi

if git diff --name-only "$CURRENT_COMMIT" "$NEW_COMMIT" | grep -q "frontend/package"; then
    warning "Frontend dependencies changed - full rebuild required"
    REBUILD_FRONTEND=true
fi

# Шаг 6: Pull изменений
log "Pulling latest changes..."
git pull origin "$BRANCH" || {
    error "Git pull failed"
    exit 1
}
success "Code updated to commit $NEW_COMMIT"

# Шаг 7: Копирование конфигов из deployed/
log "Updating configuration files..."
if [ -f "deployed/.env" ]; then
    cp deployed/.env .env
    success "Backend .env updated"
fi

if [ -f "deployed/frontend.env" ]; then
    cp deployed/frontend.env frontend/.env.production
    success "Frontend .env updated"
fi

# Шаг 8: Применение миграций БД (если есть)
if [ "$DB_MIGRATION" = true ]; then
    log "Applying database migrations..."

    # Запустить миграции через docker
    docker-compose run --rm backend alembic upgrade head || {
        error "Database migration failed!"
        log "Rolling back to commit $CURRENT_COMMIT"
        git reset --hard "$CURRENT_COMMIT"

        # Восстановление БД из бэкапа
        if [ -f "$BACKUP_FILE" ]; then
            warning "Restoring database from backup..."
            PGPASSWORD=${DB_PASSWORD:-medical2024} psql -h 172.20.0.1 -U postgres -d news_aggregator < "$BACKUP_FILE"
        fi

        exit 1
    }
    success "Database migrations applied successfully"
fi

# Шаг 9: Пересборка контейнеров
if [ "$REBUILD_BACKEND" = true ] || [ "$REBUILD_FRONTEND" = true ]; then
    log "Rebuilding Docker images..."

    if [ "$REBUILD_BACKEND" = true ]; then
        docker-compose build --no-cache backend
    fi

    if [ "$REBUILD_FRONTEND" = true ]; then
        docker-compose build --no-cache frontend
    fi

    success "Docker images rebuilt"
else
    log "Quick rebuild (no dependency changes)..."
    docker-compose build
fi

# Шаг 10: Перезапуск контейнеров
log "Restarting containers..."
docker-compose down
docker-compose up -d

# Шаг 11: Ожидание готовности
log "Waiting for services to be ready..."
sleep 30

# Проверка healthcheck
BACKEND_HEALTHY=false
FRONTEND_HEALTHY=false

for i in {1..12}; do
    if docker ps | grep -q "medical-news-backend.*healthy"; then
        BACKEND_HEALTHY=true
    fi
    if docker ps | grep -q "medical-news-frontend.*healthy"; then
        FRONTEND_HEALTHY=true
    fi

    if [ "$BACKEND_HEALTHY" = true ] && [ "$FRONTEND_HEALTHY" = true ]; then
        break
    fi

    log "Waiting for services... ($i/12)"
    sleep 5
done

if [ "$BACKEND_HEALTHY" = false ]; then
    error "Backend failed healthcheck!"
    docker logs medical-news-backend --tail 50 | tee -a "$LOG_FILE"
fi

if [ "$FRONTEND_HEALTHY" = false ]; then
    error "Frontend failed healthcheck!"
    docker logs medical-news-frontend --tail 50 | tee -a "$LOG_FILE"
fi

if [ "$BACKEND_HEALTHY" = false ] || [ "$FRONTEND_HEALTHY" = false ]; then
    error "Deployment failed - services not healthy"

    # Автоматический откат
    log "Rolling back to previous version..."
    git reset --hard "$CURRENT_COMMIT"
    docker-compose down
    docker-compose up -d

    exit 1
fi

success "All services are healthy"

# Шаг 12: Перезагрузка nginx (если конфиг изменился)
if git diff --name-only "$CURRENT_COMMIT" "$NEW_COMMIT" | grep -q "nginx"; then
    log "Reloading nginx configuration..."
    if [ -f "deployed/nginx.conf" ]; then
        sudo cp deployed/nginx.conf /etc/nginx/sites-available/medical-news
        sudo nginx -t && sudo systemctl reload nginx
        success "Nginx reloaded"
    fi
fi

# Шаг 13: Очистка старых образов
log "Cleaning up old Docker images..."
docker image prune -f

# Шаг 14: Уведомление в Telegram (опционально)
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    MESSAGE="✅ Deployment successful!

Commit: $NEW_COMMIT
Time: $(date)
Server: $(hostname)

Changes:
$(git log --oneline "$CURRENT_COMMIT".."$NEW_COMMIT" | head -5)"

    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d chat_id="$TELEGRAM_CHAT_ID" \
        -d text="$MESSAGE" > /dev/null
fi

# Итоги
log "========================================="
success "Deployment completed successfully!"
log "========================================="
log ""
log "Summary:"
log "  Previous commit: $CURRENT_COMMIT"
log "  New commit:      $NEW_COMMIT"
log "  Database backup: $BACKUP_FILE"
log "  Rebuild backend: $REBUILD_BACKEND"
log "  Rebuild frontend: $REBUILD_FRONTEND"
log "  DB migrations:   $DB_MIGRATION"
log ""
log "Services status:"
docker-compose ps | tee -a "$LOG_FILE"
log ""
log "Check logs:"
log "  docker logs medical-news-backend -f"
log "  docker logs medical-news-frontend -f"
log ""
