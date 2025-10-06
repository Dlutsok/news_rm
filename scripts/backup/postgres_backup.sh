#!/bin/bash

# PostgreSQL Backup Script for Medical News Automation System
# Создание резервных копий базы данных с ротацией

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Загрузка переменных окружения
if [ -f "$(dirname "$0")/../../.env" ]; then
    source "$(dirname "$0")/../../.env"
    log "Переменные окружения загружены из .env"
else
    warn "Файл .env не найден, используются переменные из окружения"
fi

# Конфигурация backup'а (продакшен настройки)
BACKUP_DIR="${BACKUP_DIR:-/var/backups/postgres/medical-news}"
DATABASE_URL="${DATABASE_URL:-postgresql://postgres:password@localhost:5432/news_aggregator}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
BACKUP_RETENTION_WEEKS="${BACKUP_RETENTION_WEEKS:-4}"
BACKUP_RETENTION_MONTHS="${BACKUP_RETENTION_MONTHS:-12}"

# Продакшен оптимизации
BACKUP_COMPRESSION_LEVEL="${BACKUP_COMPRESSION_LEVEL:-9}"
BACKUP_PARALLEL_JOBS="${BACKUP_PARALLEL_JOBS:-2}"

# Настройки уведомлений
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

# Парсинг DATABASE_URL
if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASSWORD="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
else
    error "Некорректный формат DATABASE_URL: $DATABASE_URL"
    exit 1
fi

# Создание директорий для backup'ов
mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly}
mkdir -p "$BACKUP_DIR"/logs

# Функция отправки уведомлений
send_notification() {
    local message="$1"
    local status="${2:-INFO}"
    
    # Telegram
    if [[ -n "$TELEGRAM_BOT_TOKEN" && -n "$TELEGRAM_CHAT_ID" ]]; then
        local emoji="ℹ️"
        case "$status" in
            "SUCCESS") emoji="✅" ;;
            "ERROR") emoji="❌" ;;
            "WARNING") emoji="⚠️" ;;
        esac
        
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
            -d chat_id="$TELEGRAM_CHAT_ID" \
            -d text="$emoji Medical News DB Backup: $message" \
            -d parse_mode="HTML" >/dev/null 2>&1 || true
    fi
    
    # Slack
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        local color="good"
        case "$status" in
            "ERROR") color="danger" ;;
            "WARNING") color="warning" ;;
        esac
        
        curl -s -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"attachments\":[{\"color\":\"$color\",\"text\":\"Medical News DB Backup: $message\"}]}" >/dev/null 2>&1 || true
    fi
}

# Функция создания backup'а
create_backup() {
    local backup_type="$1"
    local backup_subdir="$2"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/$backup_subdir/medical_news_${backup_type}_${timestamp}.sql.gz"
    local log_file="$BACKUP_DIR/logs/backup_${backup_type}_${timestamp}.log"
    
    log "Начинаем $backup_type backup базы данных $DB_NAME"
    
    # Проверка доступности базы данных
    if ! PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
        error "База данных недоступна: $DB_HOST:$DB_PORT/$DB_NAME"
        send_notification "База данных недоступна" "ERROR"
        return 1
    fi
    
    # Создание backup'а
    local start_time=$(date +%s)
    
    {
        echo "=== PostgreSQL Backup Log ==="
        echo "Timestamp: $(date)"
        echo "Database: $DB_NAME"
        echo "Host: $DB_HOST:$DB_PORT"
        echo "Backup Type: $backup_type"
        echo "Backup File: $backup_file"
        echo ""
    } > "$log_file"
    
    if PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --no-password \
        --format=custom \
        --compress="$BACKUP_COMPRESSION_LEVEL" \
        --jobs="$BACKUP_PARALLEL_JOBS" \
        --encoding=UTF8 \
        --no-owner \
        --no-privileges \
        2>> "$log_file" | gzip -"$BACKUP_COMPRESSION_LEVEL" > "$backup_file"; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local backup_size=$(du -h "$backup_file" | cut -f1)
        
        log "$backup_type backup успешно создан: $backup_file ($backup_size, ${duration}s)"
        
        {
            echo ""
            echo "=== Backup Completed Successfully ==="
            echo "Duration: ${duration} seconds"
            echo "File Size: $backup_size"
            echo "Backup Location: $backup_file"
        } >> "$log_file"
        
        # Проверка целостности backup'а
        if verify_backup "$backup_file"; then
            log "Backup прошел проверку целостности"
            send_notification "$backup_type backup создан успешно ($backup_size, ${duration}s)" "SUCCESS"
            return 0
        else
            error "Backup не прошел проверку целостности"
            send_notification "$backup_type backup поврежден!" "ERROR"
            return 1
        fi
    else
        error "Ошибка создания $backup_type backup'а"
        send_notification "$backup_type backup завершился с ошибкой" "ERROR"
        return 1
    fi
}

# Функция проверки целостности backup'а
verify_backup() {
    local backup_file="$1"
    
    info "Проверка целостности backup'а: $backup_file"
    
    # Проверка, что файл не пустой
    if [[ ! -s "$backup_file" ]]; then
        error "Backup файл пустой или не существует"
        return 1
    fi
    
    # Проверка gzip архива
    if ! gzip -t "$backup_file" 2>/dev/null; then
        error "Backup файл поврежден (ошибка gzip)"
        return 1
    fi
    
    # Проверка содержимого pg_dump
    if ! zcat "$backup_file" | head -10 | grep -q "PostgreSQL database dump" 2>/dev/null; then
        error "Backup файл не содержит корректный pg_dump"
        return 1
    fi
    
    return 0
}

# Функция ротации backup'ов
rotate_backups() {
    log "Начинаем ротацию backup'ов"
    
    # Удаление старых daily backup'ов (старше BACKUP_RETENTION_DAYS дней)
    find "$BACKUP_DIR/daily" -name "medical_news_daily_*.sql.gz" -mtime +$BACKUP_RETENTION_DAYS -delete 2>/dev/null || true
    local deleted_daily=$(find "$BACKUP_DIR/daily" -name "medical_news_daily_*.sql.gz" -mtime +$BACKUP_RETENTION_DAYS 2>/dev/null | wc -l)
    
    # Удаление старых weekly backup'ов (старше BACKUP_RETENTION_WEEKS недель)
    find "$BACKUP_DIR/weekly" -name "medical_news_weekly_*.sql.gz" -mtime +$((BACKUP_RETENTION_WEEKS * 7)) -delete 2>/dev/null || true
    local deleted_weekly=$(find "$BACKUP_DIR/weekly" -name "medical_news_weekly_*.sql.gz" -mtime +$((BACKUP_RETENTION_WEEKS * 7)) 2>/dev/null | wc -l)
    
    # Удаление старых monthly backup'ов (старше BACKUP_RETENTION_MONTHS месяцев)
    find "$BACKUP_DIR/monthly" -name "medical_news_monthly_*.sql.gz" -mtime +$((BACKUP_RETENTION_MONTHS * 30)) -delete 2>/dev/null || true
    local deleted_monthly=$(find "$BACKUP_DIR/monthly" -name "medical_news_monthly_*.sql.gz" -mtime +$((BACKUP_RETENTION_MONTHS * 30)) 2>/dev/null | wc -l)
    
    # Удаление старых логов (старше 30 дней)
    find "$BACKUP_DIR/logs" -name "backup_*.log" -mtime +30 -delete 2>/dev/null || true
    
    log "Ротация завершена. Удалено: daily($deleted_daily), weekly($deleted_weekly), monthly($deleted_monthly)"
}

# Функция получения статистики backup'ов
backup_stats() {
    local daily_count=$(find "$BACKUP_DIR/daily" -name "medical_news_daily_*.sql.gz" 2>/dev/null | wc -l)
    local weekly_count=$(find "$BACKUP_DIR/weekly" -name "medical_news_weekly_*.sql.gz" 2>/dev/null | wc -l)
    local monthly_count=$(find "$BACKUP_DIR/monthly" -name "medical_news_monthly_*.sql.gz" 2>/dev/null | wc -l)
    
    local daily_size=$(du -sh "$BACKUP_DIR/daily" 2>/dev/null | cut -f1 || echo "0")
    local weekly_size=$(du -sh "$BACKUP_DIR/weekly" 2>/dev/null | cut -f1 || echo "0")
    local monthly_size=$(du -sh "$BACKUP_DIR/monthly" 2>/dev/null | cut -f1 || echo "0")
    local total_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "0")
    
    info "Статистика backup'ов:"
    info "  Daily: $daily_count файлов ($daily_size)"
    info "  Weekly: $weekly_count файлов ($weekly_size)"
    info "  Monthly: $monthly_count файлов ($monthly_size)"
    info "  Общий размер: $total_size"
}

# Основная функция
main() {
    local backup_type="${1:-daily}"
    
    case "$backup_type" in
        "daily")
            create_backup "daily" "daily"
            ;;
        "weekly")
            create_backup "weekly" "weekly"
            ;;
        "monthly")
            create_backup "monthly" "monthly"
            ;;
        "rotate")
            rotate_backups
            ;;
        "stats")
            backup_stats
            ;;
        "verify")
            if [[ -n "${2:-}" ]]; then
                verify_backup "$2"
            else
                error "Укажите путь к backup файлу для проверки"
                exit 1
            fi
            ;;
        *)
            echo "Использование: $0 {daily|weekly|monthly|rotate|stats|verify <файл>}"
            echo ""
            echo "  daily   - Создать ежедневный backup"
            echo "  weekly  - Создать еженедельный backup"
            echo "  monthly - Создать ежемесячный backup"
            echo "  rotate  - Выполнить ротацию старых backup'ов"
            echo "  stats   - Показать статистику backup'ов"
            echo "  verify  - Проверить целостность backup файла"
            exit 1
            ;;
    esac
    
    # Выполняем ротацию после каждого backup'а
    if [[ "$backup_type" =~ ^(daily|weekly|monthly)$ ]]; then
        rotate_backups
        backup_stats
    fi
}

# Проверка зависимостей
check_dependencies() {
    local deps=("pg_dump" "pg_isready" "gzip" "find" "du")
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            error "Требуемая утилита не найдена: $dep"
            exit 1
        fi
    done
}

# Проверка прав доступа
check_permissions() {
    if [[ ! -w "$BACKUP_DIR" ]]; then
        error "Нет прав записи в директорию backup'ов: $BACKUP_DIR"
        exit 1
    fi
}

# Инициализация
init() {
    log "=== PostgreSQL Backup Script ==="
    log "База данных: $DB_NAME@$DB_HOST:$DB_PORT"
    log "Директория backup'ов: $BACKUP_DIR"
    
    check_dependencies
    check_permissions
}

# Запуск
init
main "$@"