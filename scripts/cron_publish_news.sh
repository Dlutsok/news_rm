#!/bin/bash
#
# Скрипт для запуска публикации новостей через Docker контейнер
# Используется в cron для автоматической публикации каждую минуту
#

# Логирование
LOG_DIR="/root/logs"
LOG_FILE="$LOG_DIR/publication_cron.log"

# Создаём директорию для логов если не существует
mkdir -p "$LOG_DIR"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Starting publication cron job ==="

# Проверяем что контейнер запущен
if ! docker ps --format '{{.Names}}' | grep -q "medical-news-backend"; then
    log "ERROR: Backend container is not running"
    exit 1
fi

# Запускаем скрипт публикации внутри контейнера
docker exec medical-news-backend python3 /app/scripts/publish_scheduled_news.py >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "Publication cron job completed successfully"
else
    log "ERROR: Publication cron job failed with exit code $EXIT_CODE"
fi

log "=== Finished publication cron job ==="
echo "" >> "$LOG_FILE"

exit $EXIT_CODE
