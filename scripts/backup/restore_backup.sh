#!/bin/bash

# PostgreSQL Restore Script for Medical News Automation System
# Восстановление базы данных из резервных копий

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции логирования
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

# Конфигурация
BACKUP_DIR="${BACKUP_DIR:-/var/backups/postgres/medical-news}"
DATABASE_URL="${DATABASE_URL:-postgresql://postgres:password@localhost:5432/news_aggregator}"

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

# Функция проверки backup файла
verify_backup_file() {
    local backup_file="$1"
    
    if [[ ! -f "$backup_file" ]]; then
        error "Backup файл не найден: $backup_file"
        return 1
    fi
    
    if [[ ! -s "$backup_file" ]]; then
        error "Backup файл пустой: $backup_file"
        return 1
    fi
    
    info "Проверка целостности backup файла..."
    if ! gzip -t "$backup_file" 2>/dev/null; then
        error "Backup файл поврежден (ошибка gzip): $backup_file"
        return 1
    fi
    
    if ! zcat "$backup_file" | head -10 | grep -q "PostgreSQL database dump" 2>/dev/null; then
        error "Backup файл не содержит корректный pg_dump: $backup_file"
        return 1
    fi
    
    log "Backup файл прошел проверку целостности"
    return 0
}

# Функция создания backup'а перед восстановлением
create_pre_restore_backup() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/pre_restore/medical_news_pre_restore_${timestamp}.sql.gz"
    
    mkdir -p "$BACKUP_DIR/pre_restore"
    
    log "Создание backup'а текущей БД перед восстановлением..."
    
    if PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --format=custom \
        --compress=9 \
        --encoding=UTF8 \
        --no-owner \
        --no-privileges | gzip -9 > "$backup_file"; then
        
        log "Backup перед восстановлением создан: $backup_file"
        echo "$backup_file"
        return 0
    else
        error "Не удалось создать backup перед восстановлением"
        return 1
    fi
}

# Функция восстановления из backup'а
restore_from_backup() {
    local backup_file="$1"
    local force_restore="${2:-false}"
    
    log "=== Начинаем восстановление из backup'а ==="
    log "Backup файл: $backup_file"
    log "База данных: $DB_NAME@$DB_HOST:$DB_PORT"
    
    # Проверка backup файла
    if ! verify_backup_file "$backup_file"; then
        error "Восстановление отменено из-за проблем с backup файлом"
        return 1
    fi
    
    # Проверка доступности базы данных
    if ! PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; then
        error "База данных недоступна: $DB_HOST:$DB_PORT"
        return 1
    fi
    
    # Создание backup'а перед восстановлением (если БД существует)
    local pre_restore_backup=""
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\\q" >/dev/null 2>&1; then
        if [[ "$force_restore" != "true" ]]; then
            read -p "База данных $DB_NAME существует. Создать backup перед восстановлением? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                if pre_restore_backup=$(create_pre_restore_backup); then
                    log "Pre-restore backup создан: $pre_restore_backup"
                else
                    error "Не удалось создать pre-restore backup"
                    return 1
                fi
            fi
        fi
    fi
    
    # Подтверждение восстановления
    if [[ "$force_restore" != "true" ]]; then
        warn "ВНИМАНИЕ: Восстановление полностью перезапишет базу данных $DB_NAME"
        read -p "Продолжить восстановление? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Восстановление отменено пользователем"
            return 1
        fi
    fi
    
    # Остановка подключений к базе данных
    log "Завершение активных подключений к базе данных..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c \
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid != pg_backend_pid();" >/dev/null 2>&1 || true
    
    # Удаление и пересоздание базы данных
    log "Пересоздание базы данных $DB_NAME..."
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c \
        "DROP DATABASE IF EXISTS $DB_NAME;" || {
        error "Не удалось удалить базу данных $DB_NAME"
        return 1
    }
    
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "postgres" -c \
        "CREATE DATABASE $DB_NAME WITH ENCODING='UTF8';" || {
        error "Не удалось создать базу данных $DB_NAME"
        return 1
    }
    
    # Восстановление из backup'а
    log "Восстановление данных из backup'а..."
    local start_time=$(date +%s)
    
    if zcat "$backup_file" | PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        log "Восстановление завершено успешно за ${duration} секунд"
        
        # Обновление статистики PostgreSQL
        log "Обновление статистики базы данных..."
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
            "ANALYZE;" >/dev/null 2>&1 || true
        
        # Проверка целостности восстановленной БД
        verify_restored_database
        
        return 0
    else
        error "Ошибка при восстановлении из backup'а"
        
        # Попытка восстановить pre-restore backup, если он был создан
        if [[ -n "$pre_restore_backup" && -f "$pre_restore_backup" ]]; then
            warn "Попытка восстановления из pre-restore backup..."
            restore_from_backup "$pre_restore_backup" "true"
        fi
        
        return 1
    fi
}

# Функция проверки целостности восстановленной БД
verify_restored_database() {
    log "Проверка целостности восстановленной базы данных..."
    
    # Проверка основных таблиц
    local tables=("articles" "users" "news_generation_drafts" "app_settings")
    for table in "${tables[@]}"; do
        local count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
            "SELECT COUNT(*) FROM $table;" 2>/dev/null | tr -d ' ' || echo "ERROR")
        
        if [[ "$count" == "ERROR" ]]; then
            warn "Не удалось проверить таблицу: $table"
        else
            info "Таблица $table: $count записей"
        fi
    done
    
    # Проверка версии схемы БД
    local version=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT setting_value FROM app_settings WHERE setting_key = 'db_version';" 2>/dev/null | tr -d ' ' || echo "unknown")
    
    info "Версия схемы БД: $version"
}

# Функция поиска backup'ов
list_backups() {
    local backup_type="${1:-all}"
    
    log "Доступные backup'ы:"
    
    case "$backup_type" in
        "daily"|"all")
            if [[ -d "$BACKUP_DIR/daily" ]]; then
                echo ""
                info "Daily backup'ы:"
                find "$BACKUP_DIR/daily" -name "medical_news_daily_*.sql.gz" -printf "%T@ %TY-%Tm-%Td %TH:%TM %s %p\n" 2>/dev/null | \
                    sort -nr | \
                    awk '{printf "  %s %s %s %s\n", $2, $3, $5, $6}' | \
                    head -10
            fi
            ;&
        "weekly")
            if [[ -d "$BACKUP_DIR/weekly" ]]; then
                echo ""
                info "Weekly backup'ы:"
                find "$BACKUP_DIR/weekly" -name "medical_news_weekly_*.sql.gz" -printf "%T@ %TY-%Tm-%Td %TH:%TM %s %p\n" 2>/dev/null | \
                    sort -nr | \
                    awk '{printf "  %s %s %s %s\n", $2, $3, $5, $6}' | \
                    head -5
            fi
            ;&
        "monthly")
            if [[ -d "$BACKUP_DIR/monthly" ]]; then
                echo ""
                info "Monthly backup'ы:"
                find "$BACKUP_DIR/monthly" -name "medical_news_monthly_*.sql.gz" -printf "%T@ %TY-%Tm-%Td %TH:%TM %s %p\n" 2>/dev/null | \
                    sort -nr | \
                    awk '{printf "  %s %s %s %s\n", $2, $3, $5, $6}' | \
                    head -12
            fi
            ;;
    esac
    
    if [[ -d "$BACKUP_DIR/pre_restore" ]]; then
        echo ""
        info "Pre-restore backup'ы:"
        find "$BACKUP_DIR/pre_restore" -name "medical_news_pre_restore_*.sql.gz" -printf "%T@ %TY-%Tm-%Td %TH:%TM %s %p\n" 2>/dev/null | \
            sort -nr | \
            awk '{printf "  %s %s %s %s\n", $2, $3, $5, $6}' | \
            head -5
    fi
}

# Функция интерактивного выбора backup'а
interactive_restore() {
    echo ""
    log "=== Интерактивное восстановление ==="
    
    list_backups
    
    echo ""
    read -p "Введите полный путь к backup файлу: " backup_file
    
    if [[ -z "$backup_file" ]]; then
        error "Путь к backup файлу не указан"
        return 1
    fi
    
    restore_from_backup "$backup_file"
}

# Основная функция
main() {
    local action="${1:-}"
    local backup_file="${2:-}"
    
    case "$action" in
        "restore")
            if [[ -n "$backup_file" ]]; then
                restore_from_backup "$backup_file"
            else
                interactive_restore
            fi
            ;;
        "list")
            list_backups "${2:-all}"
            ;;
        "verify")
            if [[ -n "$backup_file" ]]; then
                verify_backup_file "$backup_file"
            else
                error "Укажите путь к backup файлу для проверки"
                exit 1
            fi
            ;;
        "interactive")
            interactive_restore
            ;;
        *)
            echo "Использование: $0 {restore|list|verify|interactive} [файл]"
            echo ""
            echo "  restore <файл>  - Восстановить из указанного backup файла"
            echo "  restore         - Интерактивный выбор backup'а"
            echo "  list [тип]      - Показать доступные backup'ы (daily|weekly|monthly|all)"
            echo "  verify <файл>   - Проверить целостность backup файла"
            echo "  interactive     - Интерактивное восстановление"
            echo ""
            echo "Примеры:"
            echo "  $0 restore /path/to/backup.sql.gz"
            echo "  $0 list daily"
            echo "  $0 interactive"
            exit 1
            ;;
    esac
}

# Проверка зависимостей
check_dependencies() {
    local deps=("psql" "pg_isready" "gzip" "find")
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            error "Требуемая утилита не найдена: $dep"
            exit 1
        fi
    done
}

# Инициализация
init() {
    log "=== PostgreSQL Restore Script ==="
    log "База данных: $DB_NAME@$DB_HOST:$DB_PORT"
    log "Директория backup'ов: $BACKUP_DIR"
    
    check_dependencies
}

# Запуск
init
main "$@"