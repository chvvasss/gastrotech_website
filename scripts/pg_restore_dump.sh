#!/usr/bin/env bash
# ============================================================================
# POSTGRESQL DUMP RESTORE SCRIPT
# ============================================================================
# PURPOSE:  Restore a .sql dump file into the Docker Compose PostgreSQL
#           container safely, with pre-checks, retry logic, and verification.
# USAGE:    ./scripts/pg_restore_dump.sh [path/to/dump.sql]
#           If no path given, auto-detects dump files in repo root & backend/.
# SAFETY:   Does NOT drop existing schema; imports into existing or new DB.
#           Use --drop-first to explicitly wipe before restore.
# ============================================================================

set -euo pipefail

# ============================================================================
# CONFIGURATION & DEFAULTS
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
LOG_DIR="$REPO_ROOT/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/pg_restore_${TIMESTAMP}.log"
MAX_RETRIES=30
RETRY_INTERVAL=2
DROP_FIRST=false
TARGET_DB=""
DUMP_FILE=""

# ============================================================================
# ARGUMENT PARSING
# ============================================================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --drop-first)
            DROP_FIRST=true
            shift
            ;;
        --db)
            TARGET_DB="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS] [dump_file.sql]"
            echo ""
            echo "Options:"
            echo "  --drop-first    Drop and recreate public schema before restore"
            echo "  --db NAME       Target database name (default: auto-detect from compose)"
            echo "  -h, --help      Show this help"
            echo ""
            echo "If no dump file is specified, searches for *.sql files that look"
            echo "like pg_dump output in the repo root and backend/ directories."
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information." >&2
            exit 1
            ;;
        *)
            DUMP_FILE="$1"
            shift
            ;;
    esac
done

# ============================================================================
# COLORS & OUTPUT HELPERS
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

log()    { echo -e "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
info()   { echo -e "${CYAN}[INFO]${NC} $*" | tee -a "$LOG_FILE"; }
ok()     { echo -e "${GREEN}[OK]${NC} $*" | tee -a "$LOG_FILE"; }
warn()   { echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$LOG_FILE"; }
fail()   { echo -e "${RED}[FAIL]${NC} $*" | tee -a "$LOG_FILE"; exit 1; }

# ============================================================================
# STEP 0: SETUP LOG DIRECTORY
# ============================================================================
mkdir -p "$LOG_DIR"
echo "# pg_restore_dump.sh - started at $(date)" > "$LOG_FILE"

echo -e "\n${MAGENTA}============================================${NC}"
echo -e "${MAGENTA}  POSTGRESQL DUMP RESTORE${NC}"
echo -e "${MAGENTA}  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${MAGENTA}============================================${NC}\n"

# ============================================================================
# STEP 1: DETECT DOCKER COMPOSE COMMAND
# ============================================================================
info "[1/9] Detecting Docker Compose..."

COMPOSE_CMD=""
if docker compose version &>/dev/null; then
    COMPOSE_CMD="docker compose"
elif docker-compose version &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    fail "Neither 'docker compose' nor 'docker-compose' found. Install Docker Compose."
fi
ok "Using: $COMPOSE_CMD"

# ============================================================================
# STEP 2: LOCATE COMPOSE FILE & PARSE SETTINGS
# ============================================================================
info "[2/9] Locating docker-compose.yml..."

COMPOSE_FILE="$BACKEND_DIR/docker-compose.yml"
if [[ ! -f "$COMPOSE_FILE" ]]; then
    fail "docker-compose.yml not found at $COMPOSE_FILE"
fi
ok "Compose file: $COMPOSE_FILE"

# Detect postgres service name
cd "$BACKEND_DIR"
PG_SERVICE=$($COMPOSE_CMD config --services 2>/dev/null | grep -E '^(db|postgres|postgresql|pg)$' | head -1 || true)
if [[ -z "$PG_SERVICE" ]]; then
    # Fallback: look for service using postgres image
    PG_SERVICE=$($COMPOSE_CMD config 2>/dev/null | grep -B5 'image:.*postgres' | grep -oP '^\s+\K\S+(?=:)' | head -1 || true)
fi
if [[ -z "$PG_SERVICE" ]]; then
    fail "No PostgreSQL service found in docker-compose.yml"
fi
ok "Postgres service: $PG_SERVICE"

# Extract DB credentials from compose config
COMPOSE_CONFIG=$($COMPOSE_CMD config 2>/dev/null)

PG_USER=$(echo "$COMPOSE_CONFIG" | grep -A2 'POSTGRES_USER' | grep -oP 'POSTGRES_USER:\s*\K\S+' | head -1 || true)
[[ -z "$PG_USER" ]] && PG_USER="postgres"

PG_DB=$(echo "$COMPOSE_CONFIG" | grep -A2 'POSTGRES_DB' | grep -oP 'POSTGRES_DB:\s*\K\S+' | head -1 || true)
[[ -z "$PG_DB" ]] && PG_DB="postgres"

# Override DB if specified via --db
[[ -n "$TARGET_DB" ]] && PG_DB="$TARGET_DB"

info "Detected settings:"
info "  Service:  $PG_SERVICE"
info "  User:     $PG_USER"
info "  Database: $PG_DB"

# Check volume
HAS_VOLUME=$(echo "$COMPOSE_CONFIG" | grep -c '/var/lib/postgresql/data' || true)
if [[ "$HAS_VOLUME" -gt 0 ]]; then
    warn "Data volume detected - existing data may be present."
    warn "This script does NOT auto-wipe data. Use --drop-first to explicitly wipe."
fi

# ============================================================================
# STEP 3: FIND OR VALIDATE DUMP FILE
# ============================================================================
info "[3/9] Locating dump file..."

if [[ -n "$DUMP_FILE" ]]; then
    # User-specified dump
    if [[ ! -f "$DUMP_FILE" ]]; then
        # Try relative to repo root
        if [[ -f "$REPO_ROOT/$DUMP_FILE" ]]; then
            DUMP_FILE="$REPO_ROOT/$DUMP_FILE"
        else
            fail "Dump file not found: $DUMP_FILE"
        fi
    fi
    # Make path absolute
    DUMP_FILE="$(cd "$(dirname "$DUMP_FILE")" && pwd)/$(basename "$DUMP_FILE")"
else
    # Auto-detect: search for files that look like pg_dump output
    info "No dump file specified. Searching for candidates..."
    CANDIDATES=()

    # Search common locations
    for search_dir in "$REPO_ROOT" "$BACKEND_DIR" "$REPO_ROOT/backups" "$BACKEND_DIR/backups"; do
        [[ -d "$search_dir" ]] || continue
        while IFS= read -r -d '' f; do
            # Check if it looks like a pg_dump (first 50 lines)
            if head -50 "$f" 2>/dev/null | grep -qiE '(pg_dump|CREATE TABLE|COPY .+ FROM stdin|\\connect)'; then
                SIZE=$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null || echo "0")
                CANDIDATES+=("$f|$SIZE")
                info "  Candidate: $f ($(numfmt --to=iec "$SIZE" 2>/dev/null || echo "${SIZE}B"))"
            fi
        done < <(find "$search_dir" -maxdepth 2 -name '*.sql' -o -name '*.dump' -o -name '*.backup' 2>/dev/null | tr '\n' '\0')
    done

    if [[ ${#CANDIDATES[@]} -eq 0 ]]; then
        fail "No dump file found. Provide path as argument: $0 path/to/dump.sql"
    fi

    # Pick largest file (most likely to be a full dump)
    BEST=""
    BEST_SIZE=0
    for c in "${CANDIDATES[@]}"; do
        F="${c%%|*}"
        S="${c##*|}"
        if [[ "$S" -gt "$BEST_SIZE" ]]; then
            BEST="$F"
            BEST_SIZE="$S"
        fi
    done
    DUMP_FILE="$BEST"
fi

DUMP_SIZE=$(stat -c%s "$DUMP_FILE" 2>/dev/null || stat -f%z "$DUMP_FILE" 2>/dev/null || echo "0")
DUMP_SIZE_HUMAN=$(numfmt --to=iec "$DUMP_SIZE" 2>/dev/null || echo "${DUMP_SIZE} bytes")
ok "Dump file: $DUMP_FILE ($DUMP_SIZE_HUMAN)"

# ============================================================================
# STEP 4: ANALYZE DUMP
# ============================================================================
info "[4/9] Analyzing dump file..."

DUMP_HEAD=$(head -200 "$DUMP_FILE" 2>/dev/null || true)

HAS_CREATE_DB=false
HAS_CONNECT=false
HAS_ROLES=false
HAS_SET=false
HAS_EXTENSIONS=false
CONNECT_DB=""
REQUIRED_ROLES=()

echo "$DUMP_HEAD" | grep -qi 'CREATE DATABASE' && HAS_CREATE_DB=true
if echo "$DUMP_HEAD" | grep -qiE '\\\\connect|\\connect'; then
    HAS_CONNECT=true
    CONNECT_DB=$(echo "$DUMP_HEAD" | grep -oP '\\\\?connect\s+\K\S+' | head -1 || true)
fi
echo "$DUMP_HEAD" | grep -qiE 'CREATE ROLE|ALTER ROLE' && HAS_ROLES=true
echo "$DUMP_HEAD" | grep -qi '^SET ' && HAS_SET=true
echo "$DUMP_HEAD" | grep -qi 'CREATE EXTENSION' && HAS_EXTENSIONS=true

# Extract role names from ALTER ... OWNER TO or GRANT
while IFS= read -r role; do
    [[ -n "$role" && "$role" != "$PG_USER" && "$role" != "postgres" ]] && REQUIRED_ROLES+=("$role")
done < <(grep -oP '(OWNER TO|GRANT .+ TO)\s+\K\w+' "$DUMP_FILE" 2>/dev/null | sort -u | head -20)

info "Dump analysis:"
info "  CREATE DATABASE:  $HAS_CREATE_DB"
info "  \\connect:         $HAS_CONNECT (target: ${CONNECT_DB:-N/A})"
info "  Roles required:   ${REQUIRED_ROLES[*]:-none}"
info "  SET commands:      $HAS_SET"
info "  Extensions:        $HAS_EXTENSIONS"
info "  File size:         $DUMP_SIZE_HUMAN"

# ============================================================================
# STEP 5: ENSURE CONTAINERS ARE RUNNING
# ============================================================================
info "[5/9] Ensuring PostgreSQL container is running..."

cd "$BACKEND_DIR"

# Check if service is running
CONTAINER_STATUS=$($COMPOSE_CMD ps --format '{{.State}}' "$PG_SERVICE" 2>/dev/null || $COMPOSE_CMD ps "$PG_SERVICE" 2>/dev/null | tail -1 || true)

if ! echo "$CONTAINER_STATUS" | grep -qi 'running'; then
    info "Starting $PG_SERVICE service..."
    $COMPOSE_CMD up -d "$PG_SERVICE" 2>&1 | tee -a "$LOG_FILE"
fi

# Wait for PostgreSQL to be ready (healthcheck/retry)
info "Waiting for PostgreSQL to accept connections..."
RETRY=0
while [[ $RETRY -lt $MAX_RETRIES ]]; do
    if $COMPOSE_CMD exec -T "$PG_SERVICE" pg_isready -U "$PG_USER" -d "$PG_DB" &>/dev/null; then
        break
    fi
    RETRY=$((RETRY + 1))
    if [[ $RETRY -eq $MAX_RETRIES ]]; then
        fail "PostgreSQL did not become ready after $((MAX_RETRIES * RETRY_INTERVAL))s"
    fi
    sleep $RETRY_INTERVAL
done
ok "PostgreSQL is ready (waited ${RETRY} retries)"

# ============================================================================
# STEP 6: PRE-RESTORE SETUP
# ============================================================================
info "[6/9] Pre-restore setup..."

# 6a. Create required roles (minimum-privilege)
for role in "${REQUIRED_ROLES[@]}"; do
    info "  Creating role '$role' if not exists..."
    $COMPOSE_CMD exec -T "$PG_SERVICE" psql -U "$PG_USER" -d postgres -c \
        "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$role') THEN CREATE ROLE \"$role\" NOSUPERUSER NOCREATEDB NOCREATEROLE; END IF; END \$\$;" \
        2>&1 | tee -a "$LOG_FILE" || warn "  Could not create role '$role' (non-fatal)"
done

# 6b. Determine target DB for psql connection
RESTORE_DB="$PG_DB"
if [[ "$HAS_CONNECT" == true && -n "$CONNECT_DB" ]]; then
    info "  Dump contains \\connect $CONNECT_DB - connecting to 'postgres' initially"
    RESTORE_DB="postgres"

    # Ensure the target DB exists
    DB_EXISTS=$($COMPOSE_CMD exec -T "$PG_SERVICE" psql -U "$PG_USER" -d postgres -tAc \
        "SELECT 1 FROM pg_database WHERE datname = '$CONNECT_DB';" 2>/dev/null || true)
    if [[ "$DB_EXISTS" != "1" ]]; then
        info "  Creating database '$CONNECT_DB'..."
        $COMPOSE_CMD exec -T "$PG_SERVICE" psql -U "$PG_USER" -d postgres -c \
            "CREATE DATABASE \"$CONNECT_DB\" OWNER \"$PG_USER\";" 2>&1 | tee -a "$LOG_FILE"
    fi
elif [[ "$HAS_CREATE_DB" == true ]]; then
    info "  Dump contains CREATE DATABASE - connecting to 'postgres' initially"
    RESTORE_DB="postgres"
else
    # Verify target DB exists
    DB_EXISTS=$($COMPOSE_CMD exec -T "$PG_SERVICE" psql -U "$PG_USER" -d postgres -tAc \
        "SELECT 1 FROM pg_database WHERE datname = '$PG_DB';" 2>/dev/null || true)
    if [[ "$DB_EXISTS" != "1" ]]; then
        info "  Creating database '$PG_DB'..."
        $COMPOSE_CMD exec -T "$PG_SERVICE" psql -U "$PG_USER" -d postgres -c \
            "CREATE DATABASE \"$PG_DB\" OWNER \"$PG_USER\";" 2>&1 | tee -a "$LOG_FILE"
    fi
fi

# 6c. Optional schema drop
if [[ "$DROP_FIRST" == true ]]; then
    warn "  --drop-first: Dropping and recreating public schema on '$PG_DB'..."
    $COMPOSE_CMD exec -T "$PG_SERVICE" psql -U "$PG_USER" -d "$PG_DB" -c \
        "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO $PG_USER; GRANT ALL ON SCHEMA public TO public;" \
        2>&1 | tee -a "$LOG_FILE"
    ok "  Schema dropped and recreated"
fi

ok "Pre-restore setup complete"

# ============================================================================
# STEP 7: RESTORE
# ============================================================================
info "[7/9] Restoring dump into database '$RESTORE_DB'..."
info "  Command: cat dump.sql | $COMPOSE_CMD exec -T $PG_SERVICE psql -U $PG_USER -d $RESTORE_DB -v ON_ERROR_STOP=1"

RESTORE_START=$(date +%s)

RESTORE_EXIT=0
cat "$DUMP_FILE" | $COMPOSE_CMD exec -T "$PG_SERVICE" \
    psql -U "$PG_USER" -d "$RESTORE_DB" -v ON_ERROR_STOP=1 \
    2>&1 | tee -a "$LOG_FILE" || RESTORE_EXIT=$?

RESTORE_END=$(date +%s)
RESTORE_DURATION=$((RESTORE_END - RESTORE_START))

if [[ $RESTORE_EXIT -ne 0 ]]; then
    warn "Restore exited with code $RESTORE_EXIT (check log for errors)"
    warn "Log: $LOG_FILE"
    warn "Partial restore may have occurred. Verify below."
else
    ok "Restore completed in ${RESTORE_DURATION}s"
fi

# ============================================================================
# STEP 8: VERIFICATION
# ============================================================================
info "[8/9] Verifying restore..."

# Determine verify DB
VERIFY_DB="$PG_DB"
[[ "$HAS_CONNECT" == true && -n "$CONNECT_DB" ]] && VERIFY_DB="$CONNECT_DB"

info "  Target DB for verification: $VERIFY_DB"

# 8a. Schema list
info ""
info "  -- Schemas --"
$COMPOSE_CMD exec -T "$PG_SERVICE" psql -U "$PG_USER" -d "$VERIFY_DB" -c \
    "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog','information_schema','pg_toast');" \
    2>&1 | tee -a "$LOG_FILE"

# 8b. Table count
info ""
info "  -- Table count (user tables) --"
TABLE_COUNT=$($COMPOSE_CMD exec -T "$PG_SERVICE" psql -U "$PG_USER" -d "$VERIFY_DB" -tAc \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema');" \
    2>/dev/null || echo "?")
ok "  User tables: $TABLE_COUNT"

# 8c. Table list
info ""
info "  -- Tables --"
$COMPOSE_CMD exec -T "$PG_SERVICE" psql -U "$PG_USER" -d "$VERIFY_DB" -c \
    "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema') ORDER BY table_schema, table_name;" \
    2>&1 | tee -a "$LOG_FILE"

# 8d. Row counts for top tables
info ""
info "  -- Row counts (top 10 tables) --"
$COMPOSE_CMD exec -T "$PG_SERVICE" psql -U "$PG_USER" -d "$VERIFY_DB" -c \
    "SELECT schemaname || '.' || relname AS table_name, n_live_tup AS row_count FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 10;" \
    2>&1 | tee -a "$LOG_FILE"

# 8e. Database size
DB_SIZE=$($COMPOSE_CMD exec -T "$PG_SERVICE" psql -U "$PG_USER" -d "$VERIFY_DB" -tAc \
    "SELECT pg_size_pretty(pg_database_size('$VERIFY_DB'));" \
    2>/dev/null || echo "?")
ok "  Database size: $DB_SIZE"

# ============================================================================
# STEP 9: SUMMARY
# ============================================================================
echo "" | tee -a "$LOG_FILE"
echo -e "${GREEN}============================================${NC}" | tee -a "$LOG_FILE"
echo -e "${GREEN}  RESTORE COMPLETE${NC}" | tee -a "$LOG_FILE"
echo -e "${GREEN}============================================${NC}" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
info "Summary:"
info "  Dump file:     $DUMP_FILE"
info "  Target DB:     $VERIFY_DB"
info "  Tables:        $TABLE_COUNT"
info "  DB size:       $DB_SIZE"
info "  Duration:      ${RESTORE_DURATION}s"
info "  Exit code:     $RESTORE_EXIT"
info "  Log file:      $LOG_FILE"
echo "" | tee -a "$LOG_FILE"

if [[ $RESTORE_EXIT -ne 0 ]]; then
    warn "Restore had errors. Review the log file for details."
    exit 1
fi

exit 0
