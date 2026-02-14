# Gastrotech Backend Deployment Guide

This document covers production deployment of the Gastrotech Django backend.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Docker Production Deployment](#docker-production-deployment)
- [Database Management](#database-management)
- [Backup & Restore](#backup--restore)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker 24.0+ and Docker Compose 2.20+
- PostgreSQL 16 (or managed service like AWS RDS, Supabase)
- Redis 7 (or managed service like AWS ElastiCache)
- Domain with SSL certificate (Let's Encrypt recommended)
- Minimum 2GB RAM, 2 vCPUs

---

## Environment Variables

Create a `.env.prod` file with the following variables:

### Required Variables

```bash
# Django Core
DJANGO_SECRET_KEY=your-super-secret-key-minimum-50-chars-random
DJANGO_ALLOWED_HOSTS=gastrotech.com,www.gastrotech.com,api.gastrotech.com

# Database
POSTGRES_PASSWORD=strong-password-here
POSTGRES_USER=gastrotech
POSTGRES_DB=gastrotech

# For external managed database:
# DATABASE_URL=postgres://user:pass@host:5432/dbname

# CORS & CSRF (comma-separated)
CORS_ALLOWED_ORIGINS=https://gastrotech.com,https://www.gastrotech.com,https://admin.gastrotech.com
CSRF_TRUSTED_ORIGINS=https://gastrotech.com,https://www.gastrotech.com

# SSL
SECURE_SSL_REDIRECT=1
```

### Optional Variables

```bash
# App Version (shown in /api/v1/health/)
APP_VERSION=1.0.0

# Gunicorn Performance
GUNICORN_WORKERS=4        # Default: 4 (recommended: 2 * CPU cores + 1)
GUNICORN_THREADS=2        # Default: 2
GUNICORN_TIMEOUT=30       # Default: 30s

# Redis (if external)
REDIS_URL=redis://:password@redis-host:6379/0

# Error Tracking
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Email
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=noreply@gastrotech.com
EMAIL_HOST_PASSWORD=email-password
DEFAULT_FROM_EMAIL=Gastrotech <noreply@gastrotech.com>

# JWT Token Lifetime
JWT_ACCESS_LIFETIME_MIN=30
JWT_REFRESH_LIFETIME_DAYS=7

# Media
MAX_MEDIA_UPLOAD_BYTES=10485760  # 10MB
```

---

## Docker Production Deployment

### 1. Build and Start

```bash
# Build production image
docker compose -f docker-compose.prod.yml build

# Start all services (detached)
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f web
```

### 2. Run Migrations

Migrations are NOT run automatically in production. Run them manually:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

Or enable auto-migrations (not recommended for complex deployments):

```bash
# In docker-compose.prod.yml, set:
environment:
  - RUN_MIGRATIONS=1
```

### 3. Create Admin User

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 4. Verify Deployment

```bash
# Check health
curl https://your-domain.com/api/v1/health/

# Expected response:
# {"status":"ok","db":true,"redis":true,"version":"1.0.0","api":"v1"}
```

---

## Database Management

### Connection Pooling

Production settings include:

- `CONN_MAX_AGE=60` - Keep connections alive for 60 seconds
- `CONN_HEALTH_CHECKS=True` - Verify connections before use

For high-traffic, consider PgBouncer.

### Checking Database Size

Media files are stored in the database as binary. Monitor size:

```bash
docker compose -f docker-compose.prod.yml exec db psql -U gastrotech -c "
SELECT 
    pg_size_pretty(pg_database_size('gastrotech')) as db_size,
    pg_size_pretty(pg_total_relation_size('catalog_media')) as media_table_size;
"
```

---

## Backup & Restore

### Daily Backup Script

Create `/opt/gastrotech/backup.sh`:

```bash
#!/bin/bash
# Gastrotech PostgreSQL Backup Script
# Run via cron: 0 2 * * * /opt/gastrotech/backup.sh

set -e

BACKUP_DIR="/opt/gastrotech/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Dump database (includes media bytes)
docker compose -f /opt/gastrotech/docker-compose.prod.yml exec -T db \
    pg_dump -U gastrotech -Fc gastrotech > "$BACKUP_DIR/gastrotech_$DATE.dump"

# Compress
gzip "$BACKUP_DIR/gastrotech_$DATE.dump"

# Log success
echo "[$(date)] Backup created: gastrotech_$DATE.dump.gz" >> "$BACKUP_DIR/backup.log"

# Delete old backups
find "$BACKUP_DIR" -name "gastrotech_*.dump.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed successfully"
```

### Cron Setup

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/gastrotech/backup.sh >> /var/log/gastrotech-backup.log 2>&1
```

### Restore from Backup

```bash
# Stop web service
docker compose -f docker-compose.prod.yml stop web

# Restore database
gunzip -c /opt/gastrotech/backups/gastrotech_YYYYMMDD_HHMMSS.dump.gz | \
    docker compose -f docker-compose.prod.yml exec -T db \
    pg_restore -U gastrotech -d gastrotech --clean --if-exists

# Restart web service
docker compose -f docker-compose.prod.yml start web

# Verify
curl https://your-domain.com/api/v1/health/
```

### Retention Policy Recommendations

| Data Type | Retention | Storage Notes |
|-----------|-----------|---------------|
| Daily backups | 30 days | ~50-200MB per backup (depends on media) |
| Weekly backups | 3 months | Keep Sunday backups |
| Monthly backups | 1 year | Keep 1st of month |

### Media Size Considerations

Media is stored as binary in the `catalog_media` table. For large deployments:

1. **Current approach**: Works well up to ~10GB of media
2. **Future migration**: Consider moving to S3/MinIO for >10GB

Monitor with:

```bash
# Check media table size
docker compose -f docker-compose.prod.yml exec db psql -U gastrotech -c "
SELECT 
    count(*) as media_count,
    pg_size_pretty(sum(octet_length(data))) as total_media_size
FROM catalog_media;
"
```

---

## Monitoring

### Health Check Endpoint

The `/api/v1/health/` endpoint returns:

```json
{
  "status": "ok",       // "ok" or "degraded"
  "db": true,           // PostgreSQL connection
  "redis": true,        // Redis connection
  "version": "1.0.0",   // APP_VERSION env var
  "api": "v1"           // API version
}
```

Use for:
- Docker health checks (built into Dockerfile.prod)
- Load balancer health checks
- Uptime monitoring (Uptime Robot, Pingdom, etc.)

### Nginx Access Logs

Logs include request timing and request IDs:

```
192.168.1.1 - - [10/Jan/2026:12:00:00 +0000] "GET /api/v1/health/ HTTP/1.1" 200 89 "-" "curl/7.68.0" "-" rt=0.005 uct="0.001" uht="0.003" urt="0.004" rid=abc123-def456
```

### Gunicorn Metrics

Access logs go to stdout, viewable via:

```bash
docker compose -f docker-compose.prod.yml logs -f web
```

For Prometheus metrics, add `gunicorn[gthread]` with `statsd` exporter.

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs web

# Common issues:
# - Missing env vars: "DJANGO_SECRET_KEY is required"
# - Database not ready: Wait for pg to start
# - Port in use: Check with `lsof -i :8000`
```

### Database Connection Failed

```bash
# Test connection from web container
docker compose -f docker-compose.prod.yml exec web python -c "
import django
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT 1')
print('Database OK')
"
```

### Static Files Missing

```bash
# Rebuild static files
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput --clear
```

### Performance Issues

1. **Slow queries**: Enable query logging temporarily
2. **High memory**: Reduce `GUNICORN_WORKERS`
3. **Connection limits**: Configure PgBouncer

### Viewing Request IDs

All requests include `X-Request-ID` header in response. Use for tracing:

```bash
curl -i https://your-domain.com/api/v1/health/
# Response includes: X-Request-ID: abc123-def456
```

---

## SSL with Let's Encrypt

### Using Certbot

1. Install certbot on host
2. Stop nginx temporarily
3. Run certbot:

```bash
certbot certonly --standalone -d gastrotech.com -d www.gastrotech.com
```

4. Copy certs to Docker volume or mount point
5. Update nginx conf to use SSL

### Automatic Renewal

```bash
# Add to crontab
0 0 * * 0 certbot renew --pre-hook "docker compose -f /opt/gastrotech/docker-compose.prod.yml stop nginx" --post-hook "docker compose -f /opt/gastrotech/docker-compose.prod.yml start nginx"
```

---

## Zero-Downtime Deployment

For production updates without downtime:

```bash
# 1. Build new image
docker compose -f docker-compose.prod.yml build web

# 2. Run migrations (if needed)
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# 3. Rolling restart
docker compose -f docker-compose.prod.yml up -d --no-deps --scale web=2 web
sleep 30  # Wait for health checks
docker compose -f docker-compose.prod.yml up -d --no-deps --scale web=1 web
```

For fully automated deployments, consider Kubernetes or AWS ECS.
