#!/bin/bash

# Script to apply migrations 22 and 23
# Migration 22: Add publication tracking fields to telegram_posts
# Migration 23: Add URL to sourcetype enum

set -e  # Exit on error

echo "========================================="
echo "Applying Migrations 22-23"
echo "========================================="

# Configuration
DB_HOST="${DATABASE_HOST:-172.20.0.1}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-news_aggregator}"
DB_USER="${DATABASE_USER:-postgres}"
DB_PASSWORD="${DATABASE_PASSWORD:-medical2024}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to execute SQL
execute_sql() {
    local migration_file=$1
    local migration_name=$2

    echo -e "${YELLOW}Applying ${migration_name}...${NC}"

    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$migration_file"; then
        echo -e "${GREEN}✓ ${migration_name} applied successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to apply ${migration_name}${NC}"
        return 1
    fi
}

# Check database connection
echo "Checking database connection..."
if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Cannot connect to database${NC}"
    echo "Please check your database configuration:"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    exit 1
fi

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Apply migrations
echo ""
echo "Applying migrations..."
echo ""

# Migration 22: Add telegram_posts publication fields
execute_sql "$SCRIPT_DIR/22_add_telegram_posts_publication_fields.sql" "Migration 22 (telegram_posts fields)"

# Migration 23: Add URL to sourcetype enum
# Note: This needs to be run with autocommit, handled by the migration itself
execute_sql "$SCRIPT_DIR/23_add_url_to_sourcetype_enum.sql" "Migration 23 (URL enum value)"

echo ""
echo "========================================="
echo -e "${GREEN}All migrations applied successfully!${NC}"
echo "========================================="
echo ""

# Verify migrations
echo "Verifying migrations..."
echo ""

# Check telegram_posts columns
echo "Checking telegram_posts table structure..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'telegram_posts'
    AND column_name IN ('is_published', 'published_at', 'telegram_message_id')
    ORDER BY column_name;
"

# Check sourcetype enum values
echo ""
echo "Checking sourcetype enum values..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    SELECT enumlabel
    FROM pg_enum
    WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'sourcetype')
    ORDER BY enumlabel;
"

echo ""
echo -e "${GREEN}Verification complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Restart the backend service: docker-compose restart backend"
echo "2. Check logs: docker logs medical-news-backend -f"
echo "3. Test the /api/telegram-posts endpoints"
echo "4. Test the /api/url-articles endpoints"
