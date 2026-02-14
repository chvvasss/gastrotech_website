#!/bin/bash
set -e

# Gastrotech Production Entrypoint Script
# 
# This script handles production startup tasks:
# - Wait for database and Redis
# - Run migrations (if RUN_MIGRATIONS=1)
# - Collect static files
# - Launch Gunicorn

echo "=== Gastrotech Production Startup ==="
echo "APP_VERSION: ${APP_VERSION:-not set}"
echo "DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE}"

# Function to wait for a service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=${4:-30}
    local attempt=1

    echo "Waiting for $service_name at $host:$port..."
    
    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            echo "ERROR: $service_name not available after $max_attempts attempts"
            exit 1
        fi
        echo "Attempt $attempt/$max_attempts: $service_name not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "$service_name is ready!"
}

# Extract and wait for PostgreSQL
if [ -n "$DATABASE_URL" ]; then
    DB_HOST=$(echo "$DATABASE_URL" | sed -e 's|.*@||' -e 's|:.*||' -e 's|/.*||')
    DB_PORT=$(echo "$DATABASE_URL" | sed -e 's|.*@[^:]*:||' -e 's|/.*||')
    DB_PORT=${DB_PORT:-5432}
    wait_for_service "$DB_HOST" "$DB_PORT" "PostgreSQL"
fi

# Wait for Redis
if [ -n "$REDIS_URL" ]; then
    REDIS_HOST=$(echo "$REDIS_URL" | sed -e 's|redis://||' -e 's|:.*||')
    REDIS_PORT=$(echo "$REDIS_URL" | sed -e 's|.*://[^:]*:||' -e 's|/.*||')
    REDIS_PORT=${REDIS_PORT:-6379}
    wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"
fi

# Run migrations (optional - controlled by RUN_MIGRATIONS env var)
# In production, you may prefer running migrations separately before deploy
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput
else
    echo "Skipping migrations (RUN_MIGRATIONS!=1)"
    echo "Run migrations manually: docker compose exec web python manage.py migrate"
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear 2>/dev/null || \
    python manage.py collectstatic --noinput

# Check system
echo "Running system check..."
python manage.py check --deploy

echo "=== Startup complete, launching Gunicorn ==="

# Execute the main command
exec "$@"
