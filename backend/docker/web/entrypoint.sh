#!/bin/bash
set -e

# Gastrotech Django Entrypoint Script
# Handles database waiting, migrations, static files, and server startup

echo "=== Gastrotech Backend Startup ==="
echo "PYTHONPATH: $PYTHONPATH"
echo "Working directory: $(pwd)"
echo "DJANGO_ENV: ${DJANGO_ENV:-not set}"
echo "DEBUG: ${DEBUG:-not set}"

# Function to wait for a service to be ready
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
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo "$service_name is ready!"
}

# Extract host and port from DATABASE_URL
if [ -n "$DATABASE_URL" ]; then
    DB_HOST=$(echo "$DATABASE_URL" | sed -e 's|.*@||' -e 's|:.*||' -e 's|/.*||')
    DB_PORT=$(echo "$DATABASE_URL" | sed -e 's|.*@[^:]*:||' -e 's|/.*||')
    DB_PORT=${DB_PORT:-5432}
    wait_for_service "$DB_HOST" "$DB_PORT" "PostgreSQL"
fi

# Wait for Redis if REDIS_URL is set
if [ -n "$REDIS_URL" ]; then
    REDIS_HOST=$(echo "$REDIS_URL" | sed -e 's|redis://||' -e 's|:.*||')
    REDIS_PORT=$(echo "$REDIS_URL" | sed -e 's|.*://[^:]*:||' -e 's|/.*||')
    REDIS_PORT=${REDIS_PORT:-6379}
    wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"
fi

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Ensure dev admin exists (only in dev mode)
# Check DJANGO_ENV or DEBUG for development mode
if [ "$DJANGO_ENV" = "dev" ] || [ "$DJANGO_ENV" = "development" ] || [ "$DEBUG" = "True" ] || [ "$DEBUG" = "true" ] || [ "$DEBUG" = "1" ]; then
    echo "Development mode detected - ensuring dev admin user..."
    python manage.py ensure_dev_admin
else
    echo "Production mode - skipping dev admin creation"
fi

# Seed data if SEED_DATA is set (first-time setup)
# Usage: SEED_DATA=1 docker compose up
# Optional: SEED_SKIP_IMAGES=1 to skip image upload (faster)
#           SEED_SKIP_PDFS=1 to skip PDF import
if [ "$SEED_DATA" = "1" ] || [ "$SEED_DATA" = "true" ] || [ "$SEED_DATA" = "True" ]; then
    echo ""
    echo "=== SEED_DATA enabled - running full database setup ==="
    SEED_ARGS=""
    if [ "$SEED_SKIP_IMAGES" = "1" ]; then
        SEED_ARGS="$SEED_ARGS --skip-images"
    fi
    if [ "$SEED_SKIP_PDFS" = "1" ]; then
        SEED_ARGS="$SEED_ARGS --skip-pdfs"
    fi
    python manage.py setup_full $SEED_ARGS
    echo "=== Seed data complete ==="
    echo ""
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "=== Startup complete, launching server ==="

# Execute the main command
exec "$@"
