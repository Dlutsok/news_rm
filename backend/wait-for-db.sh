#!/bin/bash
# Скрипт ожидания готовности PostgreSQL
# Основан на dockerize функциональности

set -e

TIMEOUT=30
QUIET=0
HOST=""
PORT=""

# Функция вывода справки
usage() {
    echo "Usage: $0 host:port [options]"
    echo ""
    echo "Options:"
    echo "  --timeout=TIMEOUT    Timeout in seconds, zero for no timeout (default: 30)"
    echo "  --quiet              Don't output any status messages"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 db:5432"
    echo "  $0 172.18.0.1:5432 --timeout=60"
    echo "  $0 localhost:5432 --quiet"
}

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --timeout=*)
            TIMEOUT="${key#*=}"
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --quiet)
            QUIET=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *:*)
            if [ -z "$HOST" ]; then
                IFS=':' read -r HOST PORT <<< "$1"
            fi
            shift
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Проверка обязательных параметров
if [ -z "$HOST" ] || [ -z "$PORT" ]; then
    echo "Error: host:port is required"
    usage
    exit 1
fi

# Функция логирования
log() {
    if [ "$QUIET" -eq 0 ]; then
        echo "$@"
    fi
}

# Функция проверки подключения к PostgreSQL
check_postgres() {
    pg_isready -h "$HOST" -p "$PORT" -U "${DATABASE_USER:-postgres}" >/dev/null 2>&1
}

# Основная логика ожидания
log "Waiting for PostgreSQL at $HOST:$PORT..."

start_ts=$(date +%s)
while true; do
    if check_postgres; then
        end_ts=$(date +%s)
        log "PostgreSQL is available after $((end_ts - start_ts)) seconds"
        break
    fi

    # Проверяем таймаут
    if [ "$TIMEOUT" -gt 0 ]; then
        current_ts=$(date +%s)
        if [ $((current_ts - start_ts)) -ge "$TIMEOUT" ]; then
            log "Timeout of ${TIMEOUT}s reached, PostgreSQL at $HOST:$PORT is still not available"
            exit 1
        fi
    fi

    log "PostgreSQL is unavailable - sleeping for 2 seconds..."
    sleep 2
done

log "PostgreSQL is up - continuing..."