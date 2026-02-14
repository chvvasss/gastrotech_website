# GastroTech Deployment Guide

This guide covers deploying the GastroTech B2B platform (Django backend + Next.js admin panel) to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Deployment](#backend-deployment)
3. [Frontend Admin Deployment](#frontend-admin-deployment)
4. [Environment Variables](#environment-variables)
5. [Database Setup](#database-setup)
6. [Reverse Proxy Configuration](#reverse-proxy-configuration)
7. [Backup Strategy](#backup-strategy)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker & Docker Compose v2+
- PostgreSQL 15+ (can use Docker)
- Redis 7+ (can use Docker)
- Node.js 20+ (for frontend build)
- Domain with SSL certificate (Let's Encrypt recommended)

---

## Backend Deployment

### 1. Clone and Prepare

```bash
git clone <repository-url>
cd gastrotech.com_cursor/backend
```

### 2. Production Environment File

Create `backend/.env` with production values:

```env
# Django
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=<generate-a-strong-random-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=gastrotech
POSTGRES_USER=gastrotech
POSTGRES_PASSWORD=<strong-password>

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# CORS (frontend URL)
CORS_ALLOWED_ORIGINS=https://admin.yourdomain.com

# JWT (optional: customize expiry)
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7

# Email (optional)
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=<email-password>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Media (if using S3)
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_STORAGE_BUCKET_NAME=
# AWS_S3_REGION_NAME=

# Sentry (optional)
# SENTRY_DSN=
```

### 3. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: "3.8"

services:
  db:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build:
      context: .
      dockerfile: docker/web/Dockerfile
    restart: always
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - DJANGO_DEBUG=${DJANGO_DEBUG}
      - DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS}
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_PORT=${POSTGRES_PORT}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - REDIS_URL=${REDIS_URL}
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "127.0.0.1:8000:8000"
    command: >
      sh -c "
        python manage.py migrate --noinput &&
        python manage.py collectstatic --noinput &&
        gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2
      "

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### 4. Deploy Backend

```bash
# Build and start
docker compose -f docker-compose.prod.yml up -d --build

# Create superuser
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# View logs
docker compose -f docker-compose.prod.yml logs -f web
```

---

## Frontend Admin Deployment

### 1. Prepare Environment

Create `frontend/admin/.env.production`:

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

### 2. Build

```bash
cd frontend/admin
npm ci
npm run build
```

### 3. Deploy Options

#### Option A: Static Export (Recommended for CDN)

```bash
npm run build
# Output in .next/standalone or use next export if configured
```

#### Option B: Node.js Server

```bash
npm run build
npm run start
# Runs on port 3000 by default
```

#### Option C: Docker

Create `frontend/admin/Dockerfile`:

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

---

## Environment Variables

### Backend (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | `<random-50-char-string>` |
| `DJANGO_DEBUG` | Debug mode | `False` |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts | `api.yourdomain.com` |
| `POSTGRES_*` | Database connection | See above |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |
| `CORS_ALLOWED_ORIGINS` | CORS origins | `https://admin.yourdomain.com` |

### Frontend (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `https://api.yourdomain.com/api/v1` |

---

## Database Setup

### Initial Setup

```bash
# Apply migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser
```

### Seed Demo Data (Optional)

```bash
docker compose exec web python manage.py seed_demo_catalog
```

---

## Reverse Proxy Configuration

### Nginx Example

```nginx
# API Backend
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/backend/staticfiles/;
    }
}

# Admin Frontend
server {
    listen 443 ssl http2;
    server_name admin.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Caddy Example (Simpler)

```caddy
api.yourdomain.com {
    reverse_proxy localhost:8000
}

admin.yourdomain.com {
    reverse_proxy localhost:3000
}
```

---

## Backup Strategy

### Daily Database Backup

```bash
#!/bin/bash
# /opt/backup/backup-db.sh

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="gastrotech_${DATE}.sql.gz"

docker compose exec -T db pg_dump -U gastrotech gastrotech | gzip > "${BACKUP_DIR}/${FILENAME}"

# Keep last 30 days
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete
```

Add to crontab:

```bash
0 3 * * * /opt/backup/backup-db.sh
```

### Restore

```bash
gunzip -c backup.sql.gz | docker compose exec -T db psql -U gastrotech gastrotech
```

---

## Monitoring

### Health Checks

- Backend: `GET /api/v1/health/`
- Frontend: Check if port 3000 responds

### Recommended Tools

- **Uptime**: UptimeRobot, Healthchecks.io
- **Errors**: Sentry
- **Metrics**: Prometheus + Grafana
- **Logs**: Loki, ELK Stack

### Django Admin Monitoring

Access Django admin at `/admin/` for:
- User management
- Audit log review
- Import job status

---

## Troubleshooting

### Common Issues

#### 1. 502 Bad Gateway

- Check if backend is running: `docker compose logs web`
- Check if port 8000 is accessible

#### 2. CORS Errors

- Verify `CORS_ALLOWED_ORIGINS` matches frontend URL exactly
- Include protocol (https://)

#### 3. Static Files Not Loading

```bash
docker compose exec web python manage.py collectstatic --noinput
```

#### 4. Database Connection Failed

- Check PostgreSQL is running
- Verify credentials in .env
- Check `POSTGRES_HOST=db` (Docker service name)

#### 5. JWT Token Errors

- Ensure clocks are synchronized
- Check `ACCESS_TOKEN_LIFETIME_MINUTES` is reasonable

### Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web

# Last 100 lines
docker compose logs --tail=100 web
```

### Shell Access

```bash
# Django shell
docker compose exec web python manage.py shell

# Database shell
docker compose exec db psql -U gastrotech gastrotech

# Bash
docker compose exec web bash
```

---

## Security Checklist

- [ ] `DJANGO_DEBUG=False` in production
- [ ] Strong `DJANGO_SECRET_KEY` (50+ random characters)
- [ ] Strong database password
- [ ] HTTPS only (redirect HTTP)
- [ ] Firewall: only expose 80/443
- [ ] Regular backups tested
- [ ] Rate limiting on auth endpoints
- [ ] CORS properly configured
- [ ] Admin panel behind authentication

---

## QA Checklist

Before going live:

- [ ] Login works
- [ ] Dashboard loads correctly
- [ ] Taxonomy generation works
- [ ] Products CRUD works
- [ ] Variants CRUD works
- [ ] Media upload/reorder works
- [ ] Import dry-run and apply work
- [ ] Audit logs are recording
- [ ] Inquiries can be created and viewed
- [ ] Mobile responsive (basic)

---

## Support

For issues:
1. Check this guide's Troubleshooting section
2. Review Docker logs
3. Check Django admin for data issues
4. Review Audit Logs for recent changes
