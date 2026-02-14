# Import System Operations Runbook

**Version**: V5
**Last Updated**: 2026-01-15
**Audience**: System administrators, DevOps engineers, support staff

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Monitoring & Health Checks](#monitoring--health-checks)
3. [Operational Procedures](#operational-procedures)
4. [Limits & Quotas](#limits--quotas)
5. [Debugging Failed Jobs](#debugging-failed-jobs)
6. [Rollback & Recovery](#rollback--recovery)
7. [Snapshot Management](#snapshot-management)
8. [Performance Tuning](#performance-tuning)

---

## System Overview

### Architecture

The V5 import system follows a **two-phase commit pattern** for safe, predictable bulk operations:

```
Phase 1: VALIDATE (Dry-Run)          Phase 2: COMMIT (Execute)
┌─────────────────────────┐          ┌─────────────────────────┐
│ Upload File             │          │ Load Snapshot           │
│ ↓                       │          │ ↓                       │
│ Normalize & Validate    │          │ Verify Integrity        │
│ ↓                       │          │ ↓                       │
│ Generate Report         │          │ Create Entities         │
│ ↓                       │          │ ↓                       │
│ Create Snapshot (JSON)  │──────────▶│ DB Verification        │
│ ↓                       │          │ ↓                       │
│ Return Preview          │          │ Return Counts           │
└─────────────────────────┘          └─────────────────────────┘
```

**Key Guarantee**: `validate()` preview = `commit()` result
This is enforced through immutable snapshots with SHA-256 integrity verification.

### Core Components

#### 1. UnifiedImportService (`apps/ops/services/unified_import.py`)
- **Purpose**: Core validation and commit logic
- **Key Methods**:
  - `validate(file_bytes, filename)` - Phase 1 dry-run
  - `commit(job_id, allow_partial)` - Phase 2 execution
  - `compute_file_hash(file_bytes)` - File deduplication

#### 2. ImportJob Model (`apps/ops/models.py`)
- **Purpose**: Tracks import job state and history
- **Key Fields**:
  - `status`: pending, validating, running, success, failed, partial
  - `mode`: strict (fail on missing refs) or smart (auto-create entities)
  - `file_hash`: SHA-256 of input file for idempotency
  - `snapshot_file`: FK to Media (immutable snapshot)
  - `snapshot_hash`: SHA-256 of snapshot for integrity
  - `report_json`: Validation/execution report
  - `created_count`, `updated_count`, `error_count`: Execution metrics

#### 3. Snapshot System
- **Purpose**: Ensures deterministic behavior between validate and commit
- **Storage**: Media table (JSON files)
- **Integrity**: SHA-256 checksum verification on commit
- **Contents**: Normalized data, candidates, normalization log
- **Critical**: Commit ALWAYS reads from snapshot, NEVER from report_json

#### 4. ImportReportGenerator (`apps/ops/services/report_generator.py`)
- **Purpose**: Multi-sheet XLSX report generation
- **Sheets**:
  - Summary: Counts, status, warnings
  - Issues: Row-level errors/warnings with line numbers
  - Data: Normalized rows (re-import ready)
  - Candidates: Missing entities to create (smart mode)
  - Normalization: Merges, disambiguations

### Dependencies

- **Database**: PostgreSQL with transaction support
- **Storage**: Media table for file/snapshot persistence
- **Libraries**: pandas, openpyxl, numpy
- **Models**: Category, Series, Brand, Product, Variant

### Data Flow

```
Input File (XLSX/CSV)
  ↓
DataFrame Processing
  ↓
Normalize Empty Values (-, nan, null → None)
  ↓
Disambiguate Duplicate Model Codes (GKO-6010 → GKO-6010-2)
  ↓
Row-Level Validation
  ↓
Candidate Detection (missing entities)
  ↓
Create Snapshot (JSON)
  ↓
ImportJob Record
```

---

## Monitoring & Health Checks

### Key Metrics

Monitor these metrics for system health:

| Metric | Target | Alert Threshold | Description |
|--------|--------|-----------------|-------------|
| Job Success Rate | >95% | <90% | Percentage of jobs with status=success |
| Average Validation Time | <30s | >60s | Time from upload to validation complete |
| Average Commit Time | <2min | >5min | Time from commit start to completion |
| Error Rate | <5% | >10% | Percentage of rows with validation errors |
| Snapshot Integrity Failures | 0 | >0 | Critical: snapshot hash mismatch |
| DB Verification Failures | 0 | >0 | Critical: created entities not in DB |

### Health Check Commands

#### Check Recent Job Status
```python
# Django shell
python manage.py shell

from apps.ops.models import ImportJob
from django.utils import timezone
from datetime import timedelta

# Last 24 hours
cutoff = timezone.now() - timedelta(hours=24)
jobs = ImportJob.objects.filter(created_at__gte=cutoff)

# Status breakdown
from django.db.models import Count
status_counts = jobs.values('status').annotate(count=Count('id'))
for item in status_counts:
    print(f"{item['status']}: {item['count']}")

# Example output:
# success: 45
# failed: 2
# partial: 3
```

#### Check for Stuck Jobs
```python
from django.utils import timezone
from datetime import timedelta

# Jobs running for >30 minutes
cutoff = timezone.now() - timedelta(minutes=30)
stuck = ImportJob.objects.filter(
    status='running',
    started_at__lt=cutoff
)

for job in stuck:
    print(f"Stuck job: {job.id}, started {job.started_at}")
    # Manual intervention required
```

#### Check Snapshot Integrity
```python
import hashlib

job = ImportJob.objects.get(id='<job-id>')
if job.snapshot_file:
    snapshot_content = job.snapshot_file.bytes.decode('utf-8')
    actual_hash = hashlib.sha256(snapshot_content.encode('utf-8')).hexdigest()

    if actual_hash == job.snapshot_hash:
        print("✓ Snapshot integrity OK")
    else:
        print(f"✗ INTEGRITY FAILURE! Expected {job.snapshot_hash}, got {actual_hash}")
```

#### Check DB Verification Results
```python
job = ImportJob.objects.get(id='<job-id>')

# Check if commit included db_verify
if 'db_verify' in job.report_json:
    db_verify = job.report_json['db_verify']
    print(f"DB Verify Enabled: {db_verify.get('enabled')}")
    print(f"Entities Found: {db_verify.get('created_entities_found_in_db')}")

    if not db_verify.get('created_entities_found_in_db'):
        print("⚠ WARNING: Some entities NOT found in DB!")
        print(f"Details: {db_verify.get('verification_details')}")
```

### Log Monitoring

**Key Log Patterns**:

```bash
# Validation errors
[VALIDATE] Fatal error during validation

# Commit failures
[COMMIT] Error during commit for job

# Snapshot integrity issues
Snapshot integrity check FAILED

# DB verification failures
DB VERIFY FAILED for job
```

**Log Locations**:
- Application logs: Check Django logger output (`apps.ops.services.unified_import`)
- Database logs: PostgreSQL query logs for transaction rollbacks
- API logs: `apps.ops.import_api` for endpoint-level errors

---

## Operational Procedures

### Daily Operations

#### Morning Health Check (5 minutes)
```python
from apps.ops.models import ImportJob
from django.utils import timezone
from datetime import timedelta

# Yesterday's jobs
yesterday = timezone.now() - timedelta(days=1)
jobs = ImportJob.objects.filter(created_at__gte=yesterday)

print(f"Total jobs: {jobs.count()}")
print(f"Success: {jobs.filter(status='success').count()}")
print(f"Failed: {jobs.filter(status='failed').count()}")
print(f"Partial: {jobs.filter(status='partial').count()}")

# Review failed jobs
failed = jobs.filter(status='failed')
for job in failed:
    print(f"\nFailed Job {job.id}:")
    print(f"  User: {job.created_by.email if job.created_by else 'Unknown'}")
    print(f"  File: {job.input_file.filename if job.input_file else 'N/A'}")
    print(f"  Errors: {job.error_count}")
    # Check report_json for details
```

#### Check Failed Jobs
```python
failed_jobs = ImportJob.objects.filter(status='failed').order_by('-created_at')[:10]

for job in failed_jobs:
    print(f"\n{'='*60}")
    print(f"Job ID: {job.id}")
    print(f"Created: {job.created_at}")
    print(f"Mode: {job.mode}")
    print(f"Error Count: {job.error_count}")

    # Get first few errors
    issues = job.report_json.get('issues', [])
    errors = [i for i in issues if i.get('severity') == 'error'][:5]

    for err in errors:
        print(f"  Row {err.get('row')}: {err.get('message')}")
```

#### Review Error Logs
```python
# Common error patterns
from collections import Counter

failed_jobs = ImportJob.objects.filter(status='failed').order_by('-created_at')[:50]
error_codes = []

for job in failed_jobs:
    issues = job.report_json.get('issues', [])
    for issue in issues:
        if issue.get('severity') == 'error':
            error_codes.append(issue.get('code'))

# Top error codes
print("Top 10 error codes:")
for code, count in Counter(error_codes).most_common(10):
    print(f"{code}: {count}")
```

#### Monitor Disk Usage
```python
from apps.catalog.models import Media
from django.db.models import Sum

# Snapshot storage
snapshots = Media.objects.filter(filename__startswith='import_snapshot_')
total_size = snapshots.aggregate(Sum('size_bytes'))['size_bytes__sum'] or 0

print(f"Total snapshots: {snapshots.count()}")
print(f"Total size: {total_size / 1024 / 1024:.2f} MB")
print(f"Average size: {total_size / max(snapshots.count(), 1) / 1024:.2f} KB")
```

### Weekly Operations

#### Clean Old Snapshots (Optional)
```python
from apps.catalog.models import Media
from django.utils import timezone
from datetime import timedelta

# Delete snapshots older than 90 days
cutoff = timezone.now() - timedelta(days=90)
old_snapshots = Media.objects.filter(
    filename__startswith='import_snapshot_',
    created_at__lt=cutoff
)

print(f"Found {old_snapshots.count()} old snapshots")
# Confirm before delete
# old_snapshots.delete()
```

#### Review Candidate Patterns
```python
# Analyze what entities users are missing
from apps.ops.models import ImportJob

recent_jobs = ImportJob.objects.filter(
    mode='smart',
    created_at__gte=timezone.now() - timedelta(days=7)
)

all_candidates = {
    'categories': [],
    'series': [],
    'brands': [],
}

for job in recent_jobs:
    candidates = job.report_json.get('candidates', {})
    for entity_type in all_candidates:
        all_candidates[entity_type].extend([
            c['slug'] for c in candidates.get(entity_type, [])
        ])

# Most frequently missing entities
from collections import Counter
for entity_type, slugs in all_candidates.items():
    print(f"\nMost missing {entity_type}:")
    for slug, count in Counter(slugs).most_common(10):
        print(f"  {slug}: {count} times")
```

#### Analyze Common Errors
```python
# Group errors by type and column
error_summary = {}

recent_jobs = ImportJob.objects.filter(
    created_at__gte=timezone.now() - timedelta(days=7)
)

for job in recent_jobs:
    issues = job.report_json.get('issues', [])
    for issue in issues:
        if issue.get('severity') == 'error':
            key = (issue.get('code'), issue.get('column'))
            error_summary[key] = error_summary.get(key, 0) + 1

# Print sorted by frequency
sorted_errors = sorted(error_summary.items(), key=lambda x: x[1], reverse=True)
print("Top 15 error patterns:")
for (code, column), count in sorted_errors[:15]:
    print(f"{count:4d} | {code:30s} | {column}")
```

---

## Limits & Quotas

### Recommended Limits

| Resource | Limit | Reason |
|----------|-------|--------|
| Max File Size | 10 MB | Memory constraints during pandas processing |
| Max Rows (Products) | 5,000 | Transaction timeout risk |
| Max Rows (Variants) | 10,000 | Transaction timeout risk |
| Max Specs per Variant | 50 | JSON field size |
| Validation Timeout | 2 minutes | User experience |
| Commit Timeout | 5 minutes | Database transaction limits |

### Timeout Configuration

Default timeout is **2 minutes per phase** (validate + commit).

To adjust (if needed):
```python
# settings.py
IMPORT_VALIDATION_TIMEOUT = 120  # seconds
IMPORT_COMMIT_TIMEOUT = 300      # seconds
```

### Hard Constraints

**Database-level**:
- Product.slug: max 255 chars, globally unique
- Variant.model_code: max 100 chars, globally unique
- Series.slug: max 100 chars, globally unique (as of V5)

**Application-level**:
- Product names (title_tr/title_en): recommended <200 chars
- Variant dimensions: recommended <50 chars
- Decimal precision: max 10 digits, 2 decimal places

---

## Debugging Failed Jobs

### Finding Job Details

#### By Job ID
```python
job = ImportJob.objects.get(id='<uuid>')

print(f"Status: {job.status}")
print(f"Mode: {job.mode}")
print(f"Total rows: {job.total_rows}")
print(f"Errors: {job.error_count}")
print(f"Warnings: {job.warning_count}")
print(f"Snapshot hash: {job.snapshot_hash}")

# Full report
import json
print(json.dumps(job.report_json, indent=2))
```

#### By File Hash
```python
file_hash = '<sha256-hash>'
jobs = ImportJob.objects.filter(file_hash=file_hash).order_by('-created_at')

print(f"Found {jobs.count()} jobs with this file")
for job in jobs:
    print(f"  {job.id}: {job.status} at {job.created_at}")
```

#### By User
```python
user_email = 'user@example.com'
from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.get(email=user_email)
jobs = user.import_jobs.order_by('-created_at')[:20]

print(f"Last 20 imports by {user_email}:")
for job in jobs:
    print(f"  {job.created_at}: {job.status} ({job.total_rows} rows)")
```

### Common Failure Modes

#### 1. Validation Failures
**Symptom**: `status='failed'`, high `error_count`
**Cause**: Data quality issues (missing required fields, invalid formats)

**Investigation**:
```python
job = ImportJob.objects.get(id='<uuid>')
issues = job.report_json.get('issues', [])
errors = [i for i in issues if i.get('severity') == 'error']

# Group by error code
from collections import defaultdict
by_code = defaultdict(list)
for err in errors:
    by_code[err.get('code')].append(err)

for code, errs in by_code.items():
    print(f"\n{code}: {len(errs)} occurrences")
    print(f"  Example: Row {errs[0].get('row')}, Column {errs[0].get('column')}")
    print(f"  Message: {errs[0].get('message')}")
```

#### 2. Commit Rollback
**Symptom**: Job stuck in `running` or changed to `failed` after commit start
**Cause**: Database constraint violation, FK integrity error, transaction timeout

**Investigation**:
```python
# Check if commit was attempted
job = ImportJob.objects.get(id='<uuid>')
print(f"Started at: {job.started_at}")
print(f"Completed at: {job.completed_at}")

# Check PostgreSQL logs for constraint violations
# Look for: "duplicate key value", "foreign key constraint", "violates check constraint"
```

#### 3. Snapshot Integrity Failures
**Symptom**: Error message "Snapshot integrity check FAILED"
**Cause**: Snapshot file corrupted or modified after validation

**Investigation**:
```python
import hashlib

job = ImportJob.objects.get(id='<uuid>')
snapshot_content = job.snapshot_file.bytes.decode('utf-8')
actual_hash = hashlib.sha256(snapshot_content.encode('utf-8')).hexdigest()

print(f"Expected hash: {job.snapshot_hash}")
print(f"Actual hash:   {actual_hash}")
print(f"Match: {actual_hash == job.snapshot_hash}")

# If mismatch, snapshot is corrupt - must re-validate
```

#### 4. FK Constraint Violations
**Symptom**: Commit fails with "foreign key constraint" error
**Cause**: Referenced entity deleted between validate and commit

**Investigation**:
```python
import json

# Load snapshot
job = ImportJob.objects.get(id='<uuid>')
snapshot_content = job.snapshot_file.bytes.decode('utf-8')
snapshot = json.loads(snapshot_content)

# Check if referenced entities still exist
from apps.catalog.models import Product, Series, Brand, Category

products_data = snapshot.get('products_data', [])
for p in products_data[:5]:  # Sample
    series_slug = p.get('series_slug')
    if series_slug:
        exists = Series.objects.filter(slug=series_slug).exists()
        print(f"Series {series_slug}: {'EXISTS' if exists else 'MISSING'}")
```

### Log Analysis

**Where to find logs**:
1. Application logs: Django stdout/stderr or file-based logging
2. Database logs: PostgreSQL error log
3. API access logs: Web server logs (nginx/gunicorn)

**What to search for**:
```bash
# Validation errors
grep -i "\[VALIDATE\].*error" app.log

# Commit errors
grep -i "\[COMMIT\].*error" app.log

# Snapshot issues
grep -i "snapshot.*failed" app.log

# DB verification failures
grep -i "db verify failed" app.log

# Transaction rollbacks
grep -i "rollback" postgresql.log
```

---

## Rollback & Recovery

### Automatic Rollback

The system uses **Django transaction.atomic()** for automatic rollback on errors:

```python
# From unified_import.py
with transaction.atomic():
    # All DB writes here
    # If ANY error occurs, entire transaction rolls back
```

**This means**: Either ALL changes succeed, or NO changes are made.

### Manual Rollback

If a commit succeeded but needs to be reversed:

#### Option 1: Re-import Previous State
1. Export current state before rollback
2. Prepare file with previous values
3. Import to overwrite

#### Option 2: Direct Database Rollback (DANGEROUS)
```python
# ONLY if you have a backup and know what you're doing!
from django.db import transaction
from apps.catalog.models import Product, Variant

job = ImportJob.objects.get(id='<problematic-job-id>')

with transaction.atomic():
    # Delete created variants
    created_variants = job.report_json.get('db_verify', {}).get('created_variant_model_codes', [])
    Variant.objects.filter(model_code__in=created_variants).delete()

    # Delete created products
    created_products = job.report_json.get('db_verify', {}).get('created_product_slugs', [])
    Product.objects.filter(slug__in=created_products).delete()

    # Mark job as rolled back
    job.status = 'failed'
    job.save()
```

**WARNING**: This does NOT handle cascading deletes properly. Use with extreme caution.

### Reprocessing Failed Jobs

#### If validation failed (data quality issues):
1. Download report XLSX from job
2. Fix errors in "Issues" sheet
3. Use "Data" sheet as corrected input
4. Re-upload and validate

```python
# Frontend flow
# GET /api/admin/import-jobs/<job-id>/report/ - Download XLSX
# Fix data in Excel
# POST /api/admin/import-jobs/validate/ - Re-upload corrected file
```

#### If commit failed (transient error):
```python
# Retry same job (snapshot already exists)
job = ImportJob.objects.get(id='<uuid>')

# Reset status
job.status = 'pending'
job.save()

# Retry commit via API
# POST /api/admin/import-jobs/<job-id>/commit/
```

---

## Snapshot Management

### Snapshot Storage

**Location**: `catalog_media` table
**Format**: JSON (UTF-8 encoded)
**Naming**: `import_snapshot_<uuid>.json`
**Retention**: Manual cleanup (no auto-expiry)

**Size Estimates**:
- 100 products: ~50 KB
- 1000 variants: ~200 KB
- Typical import: 100-500 KB

### Viewing Snapshot Contents

```python
from apps.catalog.models import Media
import json

# Find snapshot
snapshot = Media.objects.get(filename='import_snapshot_<uuid>.json')

# Parse JSON
snapshot_data = json.loads(snapshot.bytes.decode('utf-8'))

# Explore structure
print("Products:", len(snapshot_data.get('products_data', [])))
print("Variants:", len(snapshot_data.get('variants_data', [])))
print("Candidates:", snapshot_data.get('candidates'))
print("Metadata:", snapshot_data.get('metadata'))
```

### Cleanup Script

```python
from apps.catalog.models import Media
from apps.ops.models import ImportJob
from django.utils import timezone
from datetime import timedelta

# Policy: Keep snapshots for 90 days
retention_days = 90
cutoff = timezone.now() - timedelta(days=retention_days)

# Find orphaned snapshots (jobs deleted but snapshot remains)
all_snapshot_ids = set(Media.objects.filter(
    filename__startswith='import_snapshot_'
).values_list('id', flat=True))

referenced_snapshot_ids = set(ImportJob.objects.filter(
    snapshot_file__isnull=False
).values_list('snapshot_file_id', flat=True))

orphaned_ids = all_snapshot_ids - referenced_snapshot_ids

print(f"Found {len(orphaned_ids)} orphaned snapshots")

# Delete old + orphaned snapshots
old_snapshots = Media.objects.filter(
    id__in=orphaned_ids,
    created_at__lt=cutoff
)

print(f"Will delete {old_snapshots.count()} old orphaned snapshots")
# Confirm before running!
# old_snapshots.delete()
```

---

## Performance Tuning

### Optimization Tips

#### 1. Use Batch Operations
The system already uses bulk operations internally:
- `Product.objects.update_or_create()` for upserts
- `Variant.objects.update_or_create()` for upserts

**Do NOT** loop with individual saves.

#### 2. Cache Warming
```python
# Load entity caches before large imports (done automatically in service)
from apps.catalog.models import Category, Series, Brand

categories = {c.slug: c for c in Category.objects.all()}
series = {s.slug: s for s in Series.objects.select_related('category').all()}
brands = {b.slug: b for b in Brand.objects.all()}
```

#### 3. Index Optimization
Ensure these indexes exist:
```sql
-- Check indexes
\d+ catalog_product
\d+ catalog_variant

-- Should include:
CREATE INDEX catalog_product_slug_idx ON catalog_product(slug);
CREATE INDEX catalog_variant_model_code_idx ON catalog_variant(model_code);
CREATE INDEX catalog_series_slug_idx ON catalog_series(slug);
CREATE UNIQUE INDEX ops_importjob_file_hash_idx ON ops_importjob(file_hash);
```

#### 4. Split Large Imports
If importing >10,000 rows:
- Split into multiple files of ~5,000 rows each
- Import sequentially
- Monitor transaction log growth

#### 5. Run During Off-Peak Hours
Large commits acquire row-level locks. Schedule during low traffic periods.

### Performance Benchmarks

**Typical Performance** (measured on AWS RDS db.t3.medium):

| Operation | Rows | Duration | Notes |
|-----------|------|----------|-------|
| Validate | 1,000 | 5-10s | Includes pandas processing |
| Validate | 5,000 | 20-30s | Memory-bound |
| Commit | 1,000 | 30-60s | DB transaction time |
| Commit | 5,000 | 2-4 min | Lock contention possible |

**If performance degrades**:
1. Check database connection pool saturation
2. Monitor PostgreSQL `pg_stat_activity` for long-running queries
3. Check table bloat: `VACUUM ANALYZE catalog_product; VACUUM ANALYZE catalog_variant;`
4. Review slow query log

---

## Emergency Procedures

### System Unresponsive During Import
```bash
# 1. Check running jobs
SELECT id, status, started_at, created_at
FROM ops_importjob
WHERE status = 'running'
ORDER BY started_at;

# 2. Identify long-running transactions
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

# 3. Kill stuck transaction (LAST RESORT)
SELECT pg_terminate_backend(<pid>);

# 4. Mark job as failed
UPDATE ops_importjob SET status = 'failed', completed_at = NOW()
WHERE id = '<stuck-job-id>';
```

### Database Out of Disk Space
```bash
# 1. Check disk usage
df -h

# 2. Clear old snapshots immediately
DELETE FROM catalog_media
WHERE filename LIKE 'import_snapshot_%'
AND created_at < NOW() - INTERVAL '30 days';

# 3. Vacuum to reclaim space
VACUUM FULL catalog_media;
```

---

## Contact & Escalation

For issues not covered in this runbook:

1. Check TROUBLESHOOTING_IMPORT.md for user-facing issues
2. Review git history for recent changes to import system
3. Consult development team with:
   - Job ID
   - Snapshot hash
   - Full error logs
   - Database query logs (if applicable)

---

**End of Operations Runbook**
