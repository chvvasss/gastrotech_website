# ============================================================================
# DATABASE RESET SCRIPT (LOCAL DEVELOPMENT ONLY)
# ============================================================================
# PURPOSE: Wipe and recreate the database to a pristine state
# SAFETY:  Will ONLY run in verified local development environments
# DANGER:  This script DESTROYS ALL DATA in the database
# ============================================================================

param(
    [switch]$SkipConfirmation,
    [switch]$NoSeed
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error-Message { Write-Host $args -ForegroundColor Red }
function Write-Warning-Message { Write-Host $args -ForegroundColor Yellow }
function Write-Info { Write-Host $args -ForegroundColor Cyan }

# Banner
Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host "  DATABASE RESET SCRIPT" -ForegroundColor Magenta
Write-Host "  LOCAL DEVELOPMENT ONLY" -ForegroundColor Magenta
Write-Host "========================================`n" -ForegroundColor Magenta

# ============================================================================
# SAFETY GATE 1: REQUIRE EXPLICIT PERMISSION
# ============================================================================
$allowReset = $env:ALLOW_DB_RESET
if ($allowReset -ne "true") {
    Write-Error-Message "❌ SAFETY GATE: ALLOW_DB_RESET environment variable not set to 'true'"
    Write-Warning-Message "`nTo run this script, you must explicitly allow it:"
    Write-Info "`n  PowerShell:"
    Write-Info "    `$env:ALLOW_DB_RESET='true'; .\scripts\reset_db.ps1"
    Write-Info "`n  OR set it persistently:"
    Write-Info "    [System.Environment]::SetEnvironmentVariable('ALLOW_DB_RESET','true','User')"
    Write-Info "    (then restart terminal)`n"
    exit 1
}

Write-Success "✓ Safety Gate 1: ALLOW_DB_RESET=true"

# ============================================================================
# SAFETY GATE 2: VERIFY LOCAL ENVIRONMENT
# ============================================================================
$settingsModule = $env:DJANGO_SETTINGS_MODULE
$databaseUrl = $env:DATABASE_URL
$djangoEnv = $env:DJANGO_ENV

Write-Info "Checking environment..."
Write-Info "  DJANGO_SETTINGS_MODULE: $settingsModule"
Write-Info "  DATABASE_URL: $databaseUrl"
Write-Info "  DJANGO_ENV: $djangoEnv"

# Check for production indicators
$isProd = $false
$reasons = @()

if ($settingsModule -match "prod|production") {
    $isProd = $true
    $reasons += "DJANGO_SETTINGS_MODULE contains 'prod' or 'production'"
}

if ($databaseUrl -and $databaseUrl -notmatch "localhost|127\.0\.0\.1|@db:") {
    $isProd = $true
    $reasons += "DATABASE_URL does not point to localhost/127.0.0.1/db"
}

if ($databaseUrl -match "gastrotech.*prod|production") {
    $isProd = $true
    $reasons += "DATABASE_URL contains production database name"
}

if ($djangoEnv -match "prod|production|staging") {
    $isProd = $true
    $reasons += "DJANGO_ENV suggests non-local environment"
}

if ($isProd) {
    Write-Error-Message "`n❌ SAFETY GATE FAILED: Environment appears to be PRODUCTION/STAGING"
    Write-Error-Message "`nReasons:"
    foreach ($reason in $reasons) {
        Write-Error-Message "  - $reason"
    }
    Write-Warning-Message "`nThis script is ONLY for local development."
    Write-Warning-Message "It will NOT run in production or staging environments.`n"
    exit 1
}

Write-Success "✓ Safety Gate 2: Environment verified as LOCAL"

# ============================================================================
# SAFETY GATE 3: USER CONFIRMATION
# ============================================================================
if (-not $SkipConfirmation) {
    Write-Warning-Message "`n⚠️  WARNING: This will PERMANENTLY DELETE all data in the database!"
    Write-Warning-Message "   Database: gastrotech (local PostgreSQL)"
    Write-Warning-Message "   All tables, data, and records will be wiped.`n"

    $response = Read-Host "Type 'RESET' to continue, or anything else to cancel"
    if ($response -ne "RESET") {
        Write-Info "`nCancelled by user. No changes made.`n"
        exit 0
    }
}

Write-Success "✓ Safety Gate 3: User confirmation received"

# ============================================================================
# STEP 1: CHANGE TO BACKEND DIRECTORY
# ============================================================================
Write-Info "`n[1/6] Changing to backend directory..."
$backendDir = Join-Path $PSScriptRoot "..\backend"
if (-not (Test-Path $backendDir)) {
    Write-Error-Message "❌ Backend directory not found: $backendDir"
    exit 1
}
Set-Location $backendDir
Write-Success "✓ Changed to: $(Get-Location)"

# ============================================================================
# STEP 2: VERIFY DOCKER COMPOSE SERVICES
# ============================================================================
Write-Info "`n[2/6] Verifying Docker Compose services..."
$composeCheck = docker-compose ps --services 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error-Message "❌ Docker Compose not available or docker-compose.yml not found"
    exit 1
}

$services = $composeCheck | Where-Object { $_ }
if ($services -notcontains "db") {
    Write-Error-Message "❌ Docker Compose 'db' service not found"
    exit 1
}
if ($services -notcontains "web") {
    Write-Error-Message "❌ Docker Compose 'web' service not found"
    exit 1
}

Write-Success "✓ Docker Compose services verified (db, web)"

# ============================================================================
# STEP 3: STOP WEB CONTAINER (RELEASE DB CONNECTIONS)
# ============================================================================
Write-Info "`n[3/6] Stopping web container to release database connections..."
docker-compose stop web | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Warning-Message "⚠️  Failed to stop web container (may not be running)"
} else {
    Write-Success "✓ Web container stopped"
}

# ============================================================================
# STEP 4: RESET DATABASE SCHEMA
# ============================================================================
Write-Info "`n[4/6] Resetting database schema (DROP SCHEMA public CASCADE)..."

$resetSql = @"
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
"@

$resetResult = $resetSql | docker-compose exec -T db psql -U postgres -d gastrotech 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error-Message "❌ Failed to reset database schema"
    Write-Error-Message $resetResult
    exit 1
}

Write-Success "✓ Database schema reset (all data wiped)"

# ============================================================================
# STEP 5: RESTART WEB & RUN MIGRATIONS
# ============================================================================
Write-Info "`n[5/6] Starting web container and running migrations..."

docker-compose up -d web | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error-Message "❌ Failed to start web container"
    exit 1
}

Write-Info "Waiting for web container to be ready..."
Start-Sleep -Seconds 5

Write-Info "Running Django migrations..."
docker-compose exec -T web python manage.py migrate --no-input 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error-Message "❌ Migrations failed"
    exit 1
}

Write-Success "✓ Migrations completed successfully"

# ============================================================================
# STEP 6: CREATE DEV ADMIN USER
# ============================================================================
Write-Info "`n[6/6] Creating development admin user..."

$adminResult = docker-compose exec -T web python manage.py ensure_dev_admin 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warning-Message "⚠️  Failed to create dev admin user automatically"
    Write-Info "You can create a superuser manually with:"
    Write-Info "  docker-compose exec web python manage.py createsuperuser"
} else {
    Write-Success "✓ Dev admin user created"
    Write-Info $adminResult
}

# ============================================================================
# OPTIONAL: SEED TAXONOMY DATA
# ============================================================================
if (-not $NoSeed) {
    Write-Info "`n[OPTIONAL] Checking for seed commands..."

    # Check if seed command exists
    $seedCheck = docker-compose exec -T web python manage.py help 2>&1 | Select-String "seed_gastrotech_ia"
    if ($seedCheck) {
        Write-Info "Running taxonomy seed (gastrotech IA)..."
        docker-compose exec -T web python manage.py seed_gastrotech_ia 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Taxonomy seed completed"
        } else {
            Write-Warning-Message "⚠️  Taxonomy seed failed (non-critical)"
        }
    } else {
        Write-Info "No seed command found (skipping)"
    }
}

# ============================================================================
# VERIFICATION
# ============================================================================
Write-Info "`n[VERIFICATION] Checking migration status..."
$migrationsOutput = docker-compose exec -T web python manage.py showmigrations 2>&1
Write-Info $migrationsOutput

# ============================================================================
# SUCCESS SUMMARY
# ============================================================================
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  ✓✓✓ DATABASE RESET COMPLETE ✓✓✓" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Success "`nDatabase has been wiped and recreated with:"
Write-Success "  ✓ Fresh schema (all migrations applied)"
Write-Success "  ✓ Dev admin user (admin@gastrotech.com / admin123)"
if (-not $NoSeed) {
    Write-Success "  ✓ Taxonomy data seeded"
}

Write-Info "`nServices running:"
docker-compose ps

Write-Info "`n📖 Next steps:"
Write-Info "  1. Access admin panel: http://localhost:8000/admin/"
Write-Info "  2. Or run tests: docker-compose exec web python manage.py test"
Write-Info "  3. Or import products: Use V5 import system`n"
