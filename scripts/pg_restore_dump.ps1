# ============================================================================
# POSTGRESQL DUMP RESTORE SCRIPT (Windows PowerShell)
# ============================================================================
# PURPOSE:  Restore a .sql dump file into the Docker Compose PostgreSQL
#           container safely, with pre-checks, retry logic, and verification.
# USAGE:    powershell -ExecutionPolicy Bypass -File scripts\pg_restore_dump.ps1 [dump.sql]
# SAFETY:   Does NOT drop existing schema; imports into existing or new DB.
#           Use -DropFirst to explicitly wipe before restore.
# ============================================================================

param(
    [Parameter(Position = 0)]
    [string]$DumpFile = "",

    [switch]$DropFirst,

    [string]$Database = "",

    [switch]$Help
)

$ErrorActionPreference = "Stop"

# ============================================================================
# HELPERS
# ============================================================================
function Write-OK      { param([string]$Msg) Write-Host "[OK]   $Msg" -ForegroundColor Green;  Add-Content -Path $script:LogFile -Value "[OK]   $Msg" }
function Write-Info    { param([string]$Msg) Write-Host "[INFO] $Msg" -ForegroundColor Cyan;   Add-Content -Path $script:LogFile -Value "[INFO] $Msg" }
function Write-Warn    { param([string]$Msg) Write-Host "[WARN] $Msg" -ForegroundColor Yellow; Add-Content -Path $script:LogFile -Value "[WARN] $Msg" }
function Write-Fail    { param([string]$Msg) Write-Host "[FAIL] $Msg" -ForegroundColor Red;    Add-Content -Path $script:LogFile -Value "[FAIL] $Msg"; exit 1 }
function Write-Banner  { param([string]$Msg) Write-Host $Msg -ForegroundColor Magenta }

# ============================================================================
# CONFIGURATION
# ============================================================================
$ScriptDir   = $PSScriptRoot
$RepoRoot    = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$BackendDir  = Join-Path $RepoRoot "backend"
$LogDir      = Join-Path $RepoRoot "logs"
$Timestamp   = Get-Date -Format "yyyyMMdd_HHmmss"
$script:LogFile = Join-Path $LogDir "pg_restore_${Timestamp}.log"
$MaxRetries  = 30
$RetryInterval = 2

# ============================================================================
# HELP
# ============================================================================
if ($Help) {
    Write-Host @"
Usage: pg_restore_dump.ps1 [OPTIONS] [dump_file.sql]

Options:
  -DumpFile <path>   Path to the .sql dump file
  -DropFirst         Drop and recreate public schema before restore
  -Database <name>   Target database name (default: auto-detect from compose)
  -Help              Show this help

If no dump file is specified, searches for *.sql files that look
like pg_dump output in the repo root and backend/ directories.
"@
    exit 0
}

# ============================================================================
# STEP 0: SETUP LOG
# ============================================================================
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
Set-Content -Path $script:LogFile -Value "# pg_restore_dump.ps1 - started at $(Get-Date)"

Write-Banner "`n============================================"
Write-Banner "  POSTGRESQL DUMP RESTORE"
Write-Banner "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Banner "============================================`n"

# ============================================================================
# STEP 1: DETECT DOCKER COMPOSE
# ============================================================================
Write-Info "[1/9] Detecting Docker Compose..."

$ComposeCmd = $null
$ComposeArgs = @()

# Try "docker compose" (v2) first
try {
    $v2Check = & docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $ComposeCmd = "docker"
        $ComposeArgs = @("compose")
    }
} catch {}

# Fallback to docker-compose (v1)
if (-not $ComposeCmd) {
    try {
        $v1Check = & docker-compose version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $ComposeCmd = "docker-compose"
            $ComposeArgs = @()
        }
    } catch {}
}

if (-not $ComposeCmd) {
    Write-Fail "Neither 'docker compose' nor 'docker-compose' found. Install Docker Compose."
}

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments)]$Arguments)
    & $ComposeCmd @ComposeArgs @Arguments
}

Write-OK "Using: $ComposeCmd $($ComposeArgs -join ' ')"

# ============================================================================
# STEP 2: LOCATE COMPOSE FILE & PARSE SETTINGS
# ============================================================================
Write-Info "[2/9] Locating docker-compose.yml..."

$ComposeFile = Join-Path $BackendDir "docker-compose.yml"
if (-not (Test-Path $ComposeFile)) {
    Write-Fail "docker-compose.yml not found at $ComposeFile"
}
Write-OK "Compose file: $ComposeFile"

Set-Location $BackendDir

# Detect postgres service
$services = Invoke-Compose config --services 2>&1
$PgService = ($services | Where-Object { $_ -match '^(db|postgres|postgresql|pg)$' } | Select-Object -First 1)
if (-not $PgService) {
    Write-Fail "No PostgreSQL service found in docker-compose.yml"
}
Write-OK "Postgres service: $PgService"

# Parse compose config for credentials
$composeConfig = (Invoke-Compose config 2>&1) -join "`n"

$PgUser = "postgres"
if ($composeConfig -match 'POSTGRES_USER:\s*(\S+)') { $PgUser = $Matches[1] }

$PgDb = "postgres"
if ($composeConfig -match 'POSTGRES_DB:\s*(\S+)') { $PgDb = $Matches[1] }

if ($Database) { $PgDb = $Database }

Write-Info "Detected settings:"
Write-Info "  Service:  $PgService"
Write-Info "  User:     $PgUser"
Write-Info "  Database: $PgDb"

# Volume check
if ($composeConfig -match '/var/lib/postgresql/data') {
    Write-Warn "Data volume detected - existing data may be present."
    Write-Warn "Use -DropFirst to explicitly wipe before restore."
}

# ============================================================================
# STEP 3: FIND OR VALIDATE DUMP FILE
# ============================================================================
Write-Info "[3/9] Locating dump file..."

if ($DumpFile) {
    if (-not (Test-Path $DumpFile)) {
        $tryPath = Join-Path $RepoRoot $DumpFile
        if (Test-Path $tryPath) {
            $DumpFile = $tryPath
        } else {
            Write-Fail "Dump file not found: $DumpFile"
        }
    }
    $DumpFile = (Resolve-Path $DumpFile).Path
} else {
    Write-Info "No dump file specified. Searching for candidates..."
    $candidates = @()
    $searchDirs = @($RepoRoot, $BackendDir, (Join-Path $RepoRoot "backups"), (Join-Path $BackendDir "backups"))

    foreach ($dir in $searchDirs) {
        if (-not (Test-Path $dir)) { continue }
        $sqlFiles = Get-ChildItem -Path $dir -Filter "*.sql" -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Length -gt 10000 }  # Likely dumps are > 10KB

        foreach ($f in $sqlFiles) {
            $header = Get-Content $f.FullName -TotalCount 50 -ErrorAction SilentlyContinue | Out-String
            if ($header -match '(pg_dump|CREATE TABLE|COPY .+ FROM stdin|\\connect)') {
                $candidates += $f
                $sizeKb = [math]::Round($f.Length / 1024, 1)
                Write-Info "  Candidate: $($f.FullName) (${sizeKb} KB)"
            }
        }
    }

    if ($candidates.Count -eq 0) {
        Write-Fail "No dump file found. Provide path as argument: .\scripts\pg_restore_dump.ps1 path\to\dump.sql"
    }

    # Pick largest
    $DumpFile = ($candidates | Sort-Object Length -Descending | Select-Object -First 1).FullName
}

$dumpInfo = Get-Item $DumpFile
$dumpSizeKb = [math]::Round($dumpInfo.Length / 1024, 1)
Write-OK "Dump file: $DumpFile ($dumpSizeKb KB)"

# ============================================================================
# STEP 4: ANALYZE DUMP
# ============================================================================
Write-Info "[4/9] Analyzing dump file..."

$dumpHead = Get-Content $DumpFile -TotalCount 200 -ErrorAction SilentlyContinue | Out-String

$HasCreateDb = $dumpHead -match 'CREATE DATABASE'
$HasConnect  = $dumpHead -match '\\connect'
$HasRoles    = $dumpHead -match '(CREATE ROLE|ALTER ROLE)'
$HasSet      = $dumpHead -match '(?m)^SET '
$HasExtensions = $dumpHead -match 'CREATE EXTENSION'

$ConnectDb = ""
if ($HasConnect -and $dumpHead -match '\\connect\s+(\S+)') { $ConnectDb = $Matches[1] }

# Extract required roles
$RequiredRoles = @()
$roleMatches = [regex]::Matches((Get-Content $DumpFile -Raw -ErrorAction SilentlyContinue), '(?:OWNER TO|GRANT .+ TO)\s+(\w+)')
$allRoles = $roleMatches | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique | Select-Object -First 20
$RequiredRoles = $allRoles | Where-Object { $_ -ne $PgUser -and $_ -ne "postgres" -and $_ -ne "public" }

Write-Info "Dump analysis:"
Write-Info "  CREATE DATABASE:  $HasCreateDb"
Write-Info "  \connect:         $HasConnect (target: $(if($ConnectDb){$ConnectDb}else{'N/A'}))"
Write-Info "  Roles required:   $(if($RequiredRoles){$RequiredRoles -join ', '}else{'none'})"
Write-Info "  SET commands:      $HasSet"
Write-Info "  Extensions:        $HasExtensions"
Write-Info "  File size:         $dumpSizeKb KB"

# ============================================================================
# STEP 5: ENSURE CONTAINER IS RUNNING
# ============================================================================
Write-Info "[5/9] Ensuring PostgreSQL container is running..."

Set-Location $BackendDir

$psOutput = Invoke-Compose ps $PgService 2>&1 | Out-String
if ($psOutput -notmatch 'running|Up') {
    Write-Info "Starting $PgService service..."
    Invoke-Compose up -d $PgService 2>&1 | Out-Null
}

# Wait for PostgreSQL ready
Write-Info "Waiting for PostgreSQL to accept connections..."
$retry = 0
while ($retry -lt $MaxRetries) {
    $ready = Invoke-Compose exec -T $PgService pg_isready -U $PgUser -d $PgDb 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) { break }
    $retry++
    if ($retry -ge $MaxRetries) {
        Write-Fail "PostgreSQL did not become ready after $($MaxRetries * $RetryInterval)s"
    }
    Start-Sleep -Seconds $RetryInterval
}
Write-OK "PostgreSQL is ready (retries: $retry)"

# ============================================================================
# STEP 6: PRE-RESTORE SETUP
# ============================================================================
Write-Info "[6/9] Pre-restore setup..."

# 6a. Create required roles
foreach ($role in $RequiredRoles) {
    Write-Info "  Creating role '$role' if not exists..."
    $roleSql = "DO `$`$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$role') THEN CREATE ROLE `"$role`" NOSUPERUSER NOCREATEDB NOCREATEROLE; END IF; END `$`$;"
    $roleSql | Invoke-Compose exec -T $PgService psql -U $PgUser -d postgres 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Warn "  Could not create role '$role' (non-fatal)" }
}

# 6b. Determine target DB
$RestoreDb = $PgDb

if ($HasConnect -and $ConnectDb) {
    Write-Info "  Dump contains \connect $ConnectDb - connecting to 'postgres' initially"
    $RestoreDb = "postgres"

    $dbExists = "SELECT 1 FROM pg_database WHERE datname = '$ConnectDb';" |
        Invoke-Compose exec -T $PgService psql -U $PgUser -d postgres -tA 2>&1
    if ($dbExists -notmatch '1') {
        Write-Info "  Creating database '$ConnectDb'..."
        "CREATE DATABASE `"$ConnectDb`" OWNER `"$PgUser`";" |
            Invoke-Compose exec -T $PgService psql -U $PgUser -d postgres 2>&1 | Out-Null
    }
} elseif ($HasCreateDb) {
    Write-Info "  Dump contains CREATE DATABASE - connecting to 'postgres' initially"
    $RestoreDb = "postgres"
} else {
    $dbExists = "SELECT 1 FROM pg_database WHERE datname = '$PgDb';" |
        Invoke-Compose exec -T $PgService psql -U $PgUser -d postgres -tA 2>&1
    if ($dbExists -notmatch '1') {
        Write-Info "  Creating database '$PgDb'..."
        "CREATE DATABASE `"$PgDb`" OWNER `"$PgUser`";" |
            Invoke-Compose exec -T $PgService psql -U $PgUser -d postgres 2>&1 | Out-Null
    }
}

# 6c. Optional schema drop
if ($DropFirst) {
    Write-Warn "  -DropFirst: Dropping and recreating public schema on '$PgDb'..."
    $dropSql = "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO $PgUser; GRANT ALL ON SCHEMA public TO public;"
    $dropSql | Invoke-Compose exec -T $PgService psql -U $PgUser -d $PgDb 2>&1 | Out-Null
    Write-OK "  Schema dropped and recreated"
}

Write-OK "Pre-restore setup complete"

# ============================================================================
# STEP 7: RESTORE
# ============================================================================
Write-Info "[7/9] Restoring dump into database '$RestoreDb'..."
Write-Info "  Reading file and piping to psql..."

$restoreStart = Get-Date

$restoreExit = 0
try {
    # PowerShell stdin pipe for docker compose exec -T
    Get-Content $DumpFile -Raw -Encoding UTF8 |
        & $ComposeCmd @ComposeArgs exec -T $PgService psql -U $PgUser -d $RestoreDb -v ON_ERROR_STOP=1 2>&1 |
        Tee-Object -FilePath $script:LogFile -Append
    $restoreExit = $LASTEXITCODE
} catch {
    $restoreExit = 1
    Write-Warn "Restore error: $_"
    Add-Content -Path $script:LogFile -Value "ERROR: $_"
}

$restoreEnd = Get-Date
$restoreDuration = [math]::Round(($restoreEnd - $restoreStart).TotalSeconds, 1)

if ($restoreExit -ne 0) {
    Write-Warn "Restore exited with code $restoreExit (check log for errors)"
    Write-Warn "Partial restore may have occurred. Verify below."
} else {
    Write-OK "Restore completed in ${restoreDuration}s"
}

# ============================================================================
# STEP 8: VERIFICATION
# ============================================================================
Write-Info "[8/9] Verifying restore..."

$VerifyDb = $PgDb
if ($HasConnect -and $ConnectDb) { $VerifyDb = $ConnectDb }
Write-Info "  Target DB for verification: $VerifyDb"

# 8a. Schemas
Write-Info "`n  -- Schemas --"
Invoke-Compose exec -T $PgService psql -U $PgUser -d $VerifyDb -c `
    "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog','information_schema','pg_toast');" 2>&1 |
    Tee-Object -FilePath $script:LogFile -Append

# 8b. Table count
$tableCount = "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema');" |
    Invoke-Compose exec -T $PgService psql -U $PgUser -d $VerifyDb -tA 2>&1
$tableCount = ($tableCount | Out-String).Trim()
Write-OK "  User tables: $tableCount"

# 8c. Table list
Write-Info "`n  -- Tables --"
Invoke-Compose exec -T $PgService psql -U $PgUser -d $VerifyDb -c `
    "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema') ORDER BY table_schema, table_name;" 2>&1 |
    Tee-Object -FilePath $script:LogFile -Append

# 8d. Row counts
Write-Info "`n  -- Row counts (top 10 tables) --"
Invoke-Compose exec -T $PgService psql -U $PgUser -d $VerifyDb -c `
    "SELECT schemaname || '.' || relname AS table_name, n_live_tup AS row_count FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 10;" 2>&1 |
    Tee-Object -FilePath $script:LogFile -Append

# 8e. DB size
$dbSize = "SELECT pg_size_pretty(pg_database_size('$VerifyDb'));" |
    Invoke-Compose exec -T $PgService psql -U $PgUser -d $VerifyDb -tA 2>&1
$dbSize = ($dbSize | Out-String).Trim()
Write-OK "  Database size: $dbSize"

# ============================================================================
# STEP 9: SUMMARY
# ============================================================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  RESTORE COMPLETE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Write-Info "Summary:"
Write-Info "  Dump file:     $DumpFile"
Write-Info "  Target DB:     $VerifyDb"
Write-Info "  Tables:        $tableCount"
Write-Info "  DB size:       $dbSize"
Write-Info "  Duration:      ${restoreDuration}s"
Write-Info "  Exit code:     $restoreExit"
Write-Info "  Log file:      $($script:LogFile)"
Write-Host ""

if ($restoreExit -ne 0) {
    Write-Warn "Restore had errors. Review the log file for details."
    exit 1
}

exit 0
