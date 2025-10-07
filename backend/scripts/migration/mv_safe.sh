#!/usr/bin/env bash

# Безопасное перемещение файлов с git mv и логированием
# Использование: ./mv_safe.sh <from> <to> [--dry-run]

set -euo pipefail

usage() {
    echo "Usage: mv_safe.sh <from> <to> [--dry-run]"
    echo "  from:     Source path"
    echo "  to:       Destination path"
    echo "  --dry-run: Show what would be done without making changes"
    exit 1
}

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Проверка аргументов
if [[ $# -lt 2 ]]; then
    usage
fi

FROM="$1"
TO="$2"
DRY_RUN="${3:-}"

# Проверка существования исходного файла/папки
if [[ ! -e "$FROM" ]]; then
    log "❌ Error: Source '$FROM' does not exist"
    exit 1
fi

# Проверка что мы в git репозитории
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log "❌ Error: Not in a git repository"
    exit 1
fi

# Создание родительской директории если нужно
TO_DIR=$(dirname "$TO")
if [[ ! -d "$TO_DIR" && "$TO_DIR" != "." ]]; then
    log "📁 Creating parent directory: $TO_DIR"
    if [[ "$DRY_RUN" != "--dry-run" ]]; then
        mkdir -p "$TO_DIR"
    fi
fi

log "📋 Plan: git mv '$FROM' -> '$TO'"

if [[ "$DRY_RUN" == "--dry-run" ]]; then
    log "🔍 DRY RUN - would execute: git mv '$FROM' '$TO'"
    exit 0
fi

# Выполнение git mv
if git mv "$FROM" "$TO"; then
    log "✅ Successfully moved: '$FROM' -> '$TO'"

    # Добавляем в git staging area если нужно
    git add "$TO" 2>/dev/null || true

    log "📝 Files staged for commit. Use 'git status' to review changes."
else
    log "❌ Failed to move '$FROM' to '$TO'"
    exit 1
fi