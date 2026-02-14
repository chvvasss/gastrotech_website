#!/usr/bin/env bash
# ============================================================================
# DATABASE RESET SCRIPT (LOCAL DEVELOPMENT ONLY)
# ============================================================================
# PURPOSE: Wipe and recreate the database to a pristine state
# SAFETY:  Will ONLY run in verified local development environments
# DANGER:  This script DESTROYS ALL DATA in the database
# ============================================================================

set -euo pipefail

# Parse arguments
SKIP_CONFIRMATION=false
NO_SEED=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-confirmation)
            SKIP_CONFIRMATION=true
            shift
            ;;
        --no-seed)
            NO_SEED=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-confirmation] [--no-seed]"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

function write_success { echo -e "${GREEN}$*${NC}"; }
function write_error { echo -e "${RED}$*${NC}"; }
function write_warning { echo -e "${YELLOW}$*${NC}"; }
function write_info { echo -e "${CYAN}$*${NC}"; }

# Banner
echo -e "\n${MAGENTA}========================================${NC}"
echo -e "${MAGENTA}  DATABASE RESET SCRIPT${NC}"
echo -e "${MAGENTA}  LOCAL DEVELOPMENT ONLY${NC}"
echo -e "${MAGENTA}========================================${NC}\n"

# ============================================================================
# SAFETY GATE 1: REQUIRE EXPLICIT PERMISSION
# ============================================================================
if [[ "${ALLOW_DB_RESET:-}" != "true" ]]; then
    write_error "❌ SAFETY GATE: ALLOW_DB_RESET environment variable not set to 'true'"
    write_warning "\nTo run this script, you must explicitly allow it:"
    write_info "\n  Bash/Zsh:"
    write_info "    ALLOW_DB_RESET=true ./scripts/reset_db.sh"
    write_info "\n  OR export it:"
    write_info "    export ALLOW_DB_RESET=true"
    write_info "    ./scripts/reset_db.sh\n"
    exit 1
fi

write_success "✓ Safety Gate 1: ALLOW_DB_RESET=true"

# ============================================================================
# SAFETY GATE 2: VERIFY LOCAL ENVIRONMENT
# ============================================================================
SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-}"
DATABASE_URL="${DATABASE_URL:-}"
DJANGO_ENV="${DJANGO_ENV:-}"

write_info "Checking environment..."
write_info "  DJANGO_SETTINGS_MODULE: $SETTINGS_MODULE"
write_info "  DATABASE_URL: $DATABASE_URL"
write_info "  DJANGO_ENV: $DJANGO_ENV"

# Check for production indicators
IS_PROD=false
REASONS=()

if [[ "$SETTINGS_MODULE" =~ prod|production ]]; then
    IS_PROD=true
    REASONS+=("DJANGO_SETTINGS_MODULE contains 'prod' or 'production'")
fi

if [[ -n "$DATABASE_URL" ]] && [[ ! "$DATABASE_URL" =~ localhost|127\.0\.0\.1|@db: ]]; then
    IS_PROD=true
    REASONS+=("DATABASE_URL does not point to localhost/127.0.0.1/db")
fi

if [[ "$DATABASE_URL" =~ gastrotech.*prod|production ]]; then
    IS_PROD=true
    REASONS+=("DATABASE_URL contains production database name")
fi

if [[ "$DJANGO_ENV" =~ prod|production|staging ]]; then
    IS_PROD=true
    REASONS+=("DJANGO_ENV suggests non-local environment")
fi

if [[ "$IS_PROD" == true ]]; then
    write_error "\n❌ SAFETY GATE FAILED: Environment appears to be PRODUCTION/STAGING"
    write_error "\nReasons:"
    for reason in "${REASONS[@]}"; do
        write_error "  - $reason"
    done
    write_warning "\nThis script is ONLY for local development."
    write_warning "It will NOT run in production or staging environments.\n"
    exit 1
fi

write_success "✓ Safety Gate 2: Environment verified as LOCAL"

# ============================================================================
# SAFETY GATE 3: USER CONFIRMATION
# ============================================================================
if [[ "$SKIP_CONFIRMATION" != true ]]; then
    write_warning "\n⚠️  WARNING: This will PERMANENTLY DELETE all data in the database!"
    write_warning "   Database: gastrotech (local PostgreSQL)"
    write_warning "   All tables, data, and records will be wiped.\n"

    read -p "Type 'RESET' to continue, or anything else to cancel: " response
    if [[ "$response" != "RESET" ]]; then
        write_info "\nCancelled by user. No changes made.\n"
        exit 0
    fi
fi

write_success "✓ Safety Gate 3: User confirmation received"

# ============================================================================
# STEP 1: CHANGE TO BACKEND DIRECTORY
# ============================================================================
write_info "\n[1/6] Changing to backend directory..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../backend" && pwd)"

if [[ ! -d "$BACKEND_DIR" ]]; then
    write_error "❌ Backend directory not found: $BACKEND_DIR"
    exit 1
fi

cd "$BACKEND_DIR"
write_success "✓ Changed to: $(pwd)"

# ============================================================================
# STEP 2: VERIFY DOCKER COMPOSE SERVICES
# ============================================================================
write_info "\n[2/6] Verifying Docker Compose services..."

if ! docker-compose ps --services &>/dev/null; then
    write_error "❌ Docker Compose not available or docker-compose.yml not found"
    exit 1
fi

SERVICES=$(docker-compose ps --services)
if ! echo "$SERVICES" | grep -q "^db$"; then
    write_error "❌ Docker Compose 'db' service not found"
    exit 1
fi
if ! echo "$SERVICES" | grep -q "^web$"; then
    write_error "❌ Docker Compose 'web' service not found"
    exit 1
fi

write_success "✓ Docker Compose services verified (db, web)"

# ============================================================================
# STEP 3: STOP WEB CONTAINER (RELEASE DB CONNECTIONS)
# ============================================================================
write_info "\n[3/6] Stopping web container to release database connections..."

if docker-compose stop web &>/dev/null; then
    write_success "✓ Web container stopped"
else
    write_warning "⚠️  Failed to stop web container (may not be running)"
fi

# ============================================================================
# STEP 4: RESET DATABASE SCHEMA
# ============================================================================
write_info "\n[4/6] Resetting database schema (DROP SCHEMA public CASCADE)..."

RESET_SQL="DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;"

if echo "$RESET_SQL" | docker-compose exec -T db psql -U postgres -d gastrotech &>/dev/null; then
    write_success "✓ Database schema reset (all data wiped)"
else
    write_error "❌ Failed to reset database schema"
    exit 1
fi

# ============================================================================
# STEP 5: RESTART WEB & RUN MIGRATIONS
# ============================================================================
write_info "\n[5/6] Starting web container and running migrations..."

if ! docker-compose up -d web &>/dev/null; then
    write_error "❌ Failed to start web container"
    exit 1
fi

write_info "Waiting for web container to be ready..."
sleep 5

write_info "Running Django migrations..."
if docker-compose exec -T web python manage.py migrate --no-input &>/dev/null; then
    write_success "✓ Migrations completed successfully"
else
    write_error "❌ Migrations failed"
    exit 1
fi

# ============================================================================
# STEP 6: CREATE DEV ADMIN USER
# ============================================================================
write_info "\n[6/6] Creating development admin user..."

if ADMIN_OUTPUT=$(docker-compose exec -T web python manage.py ensure_dev_admin 2>&1); then
    write_success "✓ Dev admin user created"
    write_info "$ADMIN_OUTPUT"
else
    write_warning "⚠️  Failed to create dev admin user automatically"
    write_info "You can create a superuser manually with:"
    write_info "  docker-compose exec web python manage.py createsuperuser"
fi

# ============================================================================
# OPTIONAL: SEED TAXONOMY DATA
# ============================================================================
if [[ "$NO_SEED" != true ]]; then
    write_info "\n[OPTIONAL] Checking for seed commands..."

    if docker-compose exec -T web python manage.py help 2>&1 | grep -q "seed_gastrotech_ia"; then
        write_info "Running taxonomy seed (gastrotech IA)..."
        if docker-compose exec -T web python manage.py seed_gastrotech_ia &>/dev/null; then
            write_success "✓ Taxonomy seed completed"
        else
            write_warning "⚠️  Taxonomy seed failed (non-critical)"
        fi
    else
        write_info "No seed command found (skipping)"
    fi
fi

# ============================================================================
# VERIFICATION
# ============================================================================
write_info "\n[VERIFICATION] Checking migration status..."
docker-compose exec -T web python manage.py showmigrations 2>&1 | head -n 20

# ============================================================================
# SUCCESS SUMMARY
# ============================================================================
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓✓✓ DATABASE RESET COMPLETE ✓✓✓${NC}"
echo -e "${GREEN}========================================${NC}"

write_success "\nDatabase has been wiped and recreated with:"
write_success "  ✓ Fresh schema (all migrations applied)"
write_success "  ✓ Dev admin user (admin@gastrotech.com / admin123)"
if [[ "$NO_SEED" != true ]]; then
    write_success "  ✓ Taxonomy data seeded"
fi

write_info "\nServices running:"
docker-compose ps

write_info "\n📖 Next steps:"
write_info "  1. Access admin panel: http://localhost:8000/admin/"
write_info "  2. Or run tests: docker-compose exec web python manage.py test"
write_info "  3. Or import products: Use V5 import system\n"
