# Database Reset Scripts

## Overview

Safe database reset scripts for **LOCAL DEVELOPMENT ONLY**. These scripts wipe all data and recreate the database from scratch with migrations applied.

## Files

- `reset_db.ps1` - PowerShell script (Windows)
- `reset_db.sh` - Bash script (Linux/Mac/Git Bash)

## Safety Features

### Triple Safety Gates

1. **Explicit Permission Flag**
   - Requires `ALLOW_DB_RESET=true` environment variable
   - Must be set before each run (does not persist by default)

2. **Environment Verification**
   - Checks `DJANGO_SETTINGS_MODULE` for "prod" or "production"
   - Checks `DATABASE_URL` is localhost/127.0.0.1/db
   - Checks `DJANGO_ENV` is not production/staging
   - **REFUSES to run if any production indicators detected**

3. **User Confirmation**
   - Requires typing "RESET" to proceed
   - Can be skipped with `--skip-confirmation` flag (use with caution)

## Usage

### PowerShell (Windows)

```powershell
# Navigate to project root
cd C:\gastrotech.com.tr.0101\gastrotech.com_cursor

# Set permission flag
$env:ALLOW_DB_RESET='true'

# Run reset
.\scripts\reset_db.ps1

# Options
.\scripts\reset_db.ps1 -SkipConfirmation  # Skip "RESET" prompt
.\scripts\reset_db.ps1 -NoSeed            # Skip taxonomy seeding
```

**PowerShell Execution Policy**: If script fails with "cannot be loaded because running scripts is disabled", run with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset_db.ps1
```

Or set environment flag first:

```powershell
$env:ALLOW_DB_RESET='true'
powershell -ExecutionPolicy Bypass -File .\scripts\reset_db.ps1
```

### Bash (Linux/Mac/Git Bash)

```bash
# Navigate to project root
cd /path/to/gastrotech.com_cursor

# Make executable (first time only)
chmod +x scripts/reset_db.sh

# Set permission and run
ALLOW_DB_RESET=true ./scripts/reset_db.sh

# Options
ALLOW_DB_RESET=true ./scripts/reset_db.sh --skip-confirmation
ALLOW_DB_RESET=true ./scripts/reset_db.sh --no-seed
```

## What It Does

### Step-by-Step Process

1. **Safety Checks**
   - Validates ALLOW_DB_RESET=true
   - Verifies local environment (not production/staging)
   - Gets user confirmation

2. **Database Reset**
   - Stops web container (releases DB connections)
   - Executes: `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
   - Restarts web container

3. **Migrations**
   - Runs all Django migrations from scratch
   - Clean schema with all models created

4. **Admin User**
   - Creates development superuser
   - Email: `admin@gastrotech.com`
   - Password: `admin123`

5. **Seeding (Optional)**
   - Seeds taxonomy data if `seed_gastrotech_ia` command exists
   - Can be skipped with `--no-seed` flag

## Verification

After running the reset script:

```bash
# Check migration status
docker-compose exec web python manage.py showmigrations

# Check services running
docker-compose ps

# Test admin login
# Open: http://localhost:8000/admin/
# Email: admin@gastrotech.com
# Password: admin123
```

## Troubleshooting

### "SAFETY GATE: ALLOW_DB_RESET not set"

**Fix**: Set the environment variable before running:

```powershell
# PowerShell
$env:ALLOW_DB_RESET='true'
.\scripts\reset_db.ps1
```

```bash
# Bash
ALLOW_DB_RESET=true ./scripts/reset_db.sh
```

### "SAFETY GATE FAILED: Environment appears to be PRODUCTION"

**Cause**: Script detected production indicators in environment variables.

**Fix**: This is intentional protection. Verify your environment:

```powershell
# Check environment variables
echo $env:DJANGO_SETTINGS_MODULE
echo $env:DATABASE_URL
echo $env:DJANGO_ENV
```

Ensure:
- `DJANGO_SETTINGS_MODULE` does NOT contain "prod" or "production"
- `DATABASE_URL` points to localhost/127.0.0.1/db
- `DJANGO_ENV` is "dev" or not set

### "Docker Compose 'db' service not found"

**Cause**: Docker Compose not available or not in backend directory.

**Fix**:

```bash
cd backend
docker-compose ps --services
```

Expected output: `db`, `redis`, `web`

### "Failed to reset database schema"

**Cause**: Database connection issue or permissions.

**Fix**:

```bash
# Verify DB container is running
docker-compose ps

# Check DB logs
docker-compose logs db

# Manually test connection
docker-compose exec db psql -U postgres -d gastrotech -c "SELECT 1"
```

### PowerShell Script Won't Run

**Cause**: Execution policy restriction.

**Fix**:

```powershell
# Option 1: Bypass for this script only
powershell -ExecutionPolicy Bypass -File .\scripts\reset_db.ps1

# Option 2: Set policy for current user (permanent)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Warning

**THIS IS A DESTRUCTIVE OPERATION**

- All data in the database will be PERMANENTLY DELETED
- Cannot be undone
- Only use in local development
- Never use in production or staging
- Always verify environment before running

## Advanced Usage

### Reset Without Seeding

If you want a completely empty database without taxonomy data:

```powershell
# PowerShell
.\scripts\reset_db.ps1 -NoSeed

# Bash
./scripts/reset_db.sh --no-seed
```

### Automated Reset (CI/Testing)

For automated environments (e.g., CI pipelines):

```bash
# Set flag and skip confirmation
ALLOW_DB_RESET=true ./scripts/reset_db.sh --skip-confirmation --no-seed
```

### Manual Reset Steps

If scripts fail, you can manually reset:

```bash
cd backend

# Stop web container
docker-compose stop web

# Reset schema
docker-compose exec db psql -U postgres -d gastrotech -c "
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
"

# Restart and migrate
docker-compose up -d web
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py ensure_dev_admin
```

## Support

See also: `RUNBOOK_LOCAL_TEST_AND_BUILD.md` section 5 (Database Reset)

For issues or questions, check the project documentation or contact the development team.
