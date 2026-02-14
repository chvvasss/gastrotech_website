# GASTROTECH PRODUCTION DEPLOYMENT RUNBOOK
## Security-Hardened Deployment Guide

**Version:** 1.0
**Last Updated:** 2026-01-24
**Author:** Principal Application Security Engineer

---

## PRE-DEPLOYMENT CHECKLIST

### 1. Environment Variables (CRITICAL)

Create `.env.prod` with the following REQUIRED variables:

```bash
# CRITICAL - Must be unique and secure
DJANGO_SECRET_KEY=<generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">

# Database
POSTGRES_USER=gastrotech_prod
POSTGRES_PASSWORD=<strong-password-32chars>
POSTGRES_DB=gastrotech
DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}

# Redis
REDIS_URL=redis://redis:6379/0

# Django
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=gastrotech.com,www.gastrotech.com,api.gastrotech.com
DJANGO_SETTINGS_MODULE=config.settings.prod

# Security
SECURE_SSL_REDIRECT=1
CORS_ALLOWED_ORIGINS=https://gastrotech.com,https://www.gastrotech.com
CSRF_TRUSTED_ORIGINS=https://gastrotech.com,https://www.gastrotech.com

# Error Tracking (Optional but recommended)
SENTRY_DSN=<your-sentry-dsn>
SENTRY_ENVIRONMENT=production

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=<email>
EMAIL_HOST_PASSWORD=<app-password>
DEFAULT_FROM_EMAIL=noreply@gastrotech.com
```

### 2. Secret Rotation

If any secrets were exposed in git history:

```bash
# Generate new Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate strong database password
openssl rand -base64 32
```

### 3. Security Scan Results

Before deployment, ensure these pass:

```bash
# Backend security checks
cd backend
pip install bandit safety

# Run security linter
bandit -r apps/ -ll

# Check for vulnerable dependencies
safety check -r requirements.txt

# Django deployment check
python manage.py check --deploy
```

Expected output for `check --deploy`:
- No critical warnings
- All security settings properly configured

---

## DEPLOYMENT STEPS

### Step 1: Prepare Infrastructure

```bash
# Create Docker volumes
docker volume create gastrotech_postgres_data
docker volume create gastrotech_redis_data
docker volume create gastrotech_static_volume
docker volume create gastrotech_media_volume
```

### Step 2: Build Production Images

```bash
cd backend

# Build production image
docker build -f docker/web/Dockerfile.prod -t gastrotech-backend:latest .

# Verify image
docker images gastrotech-backend:latest
```

### Step 3: Deploy Stack

```bash
# Deploy with production compose
docker compose -f docker-compose.prod.yml up -d

# Verify services are running
docker compose -f docker-compose.prod.yml ps
```

### Step 4: Run Migrations

```bash
# Apply database migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput

# Collect static files
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Step 5: Create Admin User

```bash
# Create superuser (interactive)
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### Step 6: Verify Deployment

```bash
# Health check
curl -f https://api.gastrotech.com/api/v1/health/

# Expected response:
# {"status": "healthy", "version": "1.0.0"}
```

---

## POST-DEPLOYMENT VERIFICATION

### Security Headers Check

```bash
# Check security headers
curl -I https://gastrotech.com

# Expected headers:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Referrer-Policy: strict-origin-when-cross-origin
# Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
# Content-Security-Policy: default-src 'self'; ...
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

### Rate Limiting Verification

```bash
# Test login rate limiting (should get 429 after 5 attempts)
for i in {1..7}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST https://api.gastrotech.com/api/v1/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
done

# Expected: 401 401 401 401 401 429 429
```

### API Docs Access (Should be blocked in production)

```bash
curl -I https://api.gastrotech.com/api/v1/docs/
# Expected: 404 Not Found
```

---

## BACKUP PROCEDURES

### Database Backup

```bash
# Create backup
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U gastrotech_prod gastrotech > backup_$(date +%Y%m%d).sql

# Compress backup
gzip backup_$(date +%Y%m%d).sql

# Verify backup
gunzip -c backup_$(date +%Y%m%d).sql.gz | head -100
```

### Automated Daily Backup Script

```bash
#!/bin/bash
# /opt/gastrotech/backup.sh
set -e

BACKUP_DIR=/opt/gastrotech/backups
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/gastrotech_${DATE}.sql.gz"

# Create backup
docker compose -f /opt/gastrotech/docker-compose.prod.yml exec -T db \
  pg_dump -U gastrotech_prod gastrotech | gzip > "${BACKUP_FILE}"

# Keep only last 7 days
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_FILE}"
```

Add to crontab:
```bash
0 2 * * * /opt/gastrotech/backup.sh >> /var/log/gastrotech-backup.log 2>&1
```

---

## ROLLBACK PROCEDURES

### Quick Rollback

```bash
# Stop current deployment
docker compose -f docker-compose.prod.yml down

# Restore previous image
docker tag gastrotech-backend:previous gastrotech-backend:latest

# Restart
docker compose -f docker-compose.prod.yml up -d
```

### Database Rollback

```bash
# CAUTION: This will overwrite current data
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U gastrotech_prod gastrotech < backup_YYYYMMDD.sql
```

---

## MONITORING CHECKLIST

### Essential Alerts to Configure

1. **5xx Error Rate** > 1% in 5 minutes
2. **Response Time** > 2s p95
3. **Login Failure Rate** > 10 in 5 minutes
4. **Disk Usage** > 80%
5. **Memory Usage** > 90%
6. **Database Connections** > 80% of max

### Health Endpoint Monitoring

Monitor `/api/v1/health/` every 30 seconds:
- Expected: 200 OK
- Alert: 3 consecutive failures

---

## EMERGENCY CONTACTS

| Role | Contact | Escalation Time |
|------|---------|-----------------|
| On-Call Engineer | [TBD] | Immediate |
| Security Lead | [TBD] | 15 min |
| DB Admin | [TBD] | 30 min |

---

## SECURITY INCIDENT RESPONSE

### Suspected Breach

1. **Isolate**: Block suspicious IPs via nginx/firewall
2. **Preserve**: Capture logs before rotation
3. **Assess**: Check auth logs for unusual patterns
4. **Rotate**: Change all secrets
5. **Report**: Notify security team

### Log Locations

```bash
# Django logs
docker compose logs web

# Nginx logs
docker compose logs nginx

# Database logs
docker compose logs db
```

---

## APPENDIX: Security Configuration Summary

| Setting | Value | Location |
|---------|-------|----------|
| HTTPS Redirect | Enabled | prod.py |
| HSTS | 1 year + preload | prod.py |
| Session Cookie Secure | True | prod.py |
| CSRF Cookie Secure | True | prod.py |
| X-Frame-Options | DENY | nginx.conf |
| CSP | Strict | nginx.conf |
| Login Rate Limit | 5/min | accounts/views.py |
| API Rate Limit | 10/s | nginx.conf |
| API Docs | Disabled in prod | api/v1/urls.py |
