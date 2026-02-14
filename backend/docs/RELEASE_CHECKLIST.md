# Gastrotech Backend Release Checklist

Use this checklist before deploying to production.

---

## Pre-Deployment Checklist

### Code Quality

- [ ] All tests pass locally: `docker compose exec web python manage.py test`
- [ ] No linting errors: `ruff check .`
- [ ] Code is formatted: `black --check .`
- [ ] CI pipeline passes (GitHub Actions)
- [ ] No `TODO` or `FIXME` in critical paths
- [ ] Security scan passes: `bandit -r apps/`

### Environment

- [ ] `.env.prod` file created with all required variables
- [ ] `DJANGO_SECRET_KEY` is unique and strong (50+ chars)
- [ ] `DJANGO_ALLOWED_HOSTS` set correctly
- [ ] `CORS_ALLOWED_ORIGINS` set to production domains
- [ ] `CSRF_TRUSTED_ORIGINS` set to production domains
- [ ] `DATABASE_URL` points to production database
- [ ] `REDIS_URL` points to production Redis
- [ ] `APP_VERSION` set to release version

### Database

- [ ] Backup current database before migration
- [ ] Migrations tested on staging
- [ ] `python manage.py makemigrations --check` shows no new migrations

### SSL/Security

- [ ] SSL certificate valid and not expiring soon
- [ ] `SECURE_SSL_REDIRECT=1` in production
- [ ] HSTS headers enabled
- [ ] CORS and CSRF properly configured

---

## Deployment Steps

1. **Tag the release**
   ```bash
   git tag -a v1.0.0 -m "Release 1.0.0"
   git push origin v1.0.0
   ```

2. **Build production image**
   ```bash
   docker compose -f docker-compose.prod.yml build
   ```

3. **Run migrations**
   ```bash
   docker compose -f docker-compose.prod.yml exec web python manage.py migrate
   ```

4. **Deploy**
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

5. **Verify deployment** (see Smoke Test below)

---

## Smoke Test Checklist

Run these checks immediately after deployment:

### System Health

| # | Test | Command/URL | Expected |
|---|------|-------------|----------|
| 1 | Health check | `curl https://api.gastrotech.com/api/v1/health/` | `{"status":"ok","db":true,"redis":true}` |
| 2 | Swagger UI loads | `https://api.gastrotech.com/api/v1/docs/` | Page loads, shows API docs |
| 3 | OpenAPI schema | `https://api.gastrotech.com/api/v1/schema/` | Returns YAML/JSON schema |

### Public Endpoints (No Auth)

| # | Test | Command | Expected |
|---|------|---------|----------|
| 4 | Navigation | `curl https://api.gastrotech.com/api/v1/nav/` | 200 OK, returns categories + series |
| 5 | Category tree | `curl https://api.gastrotech.com/api/v1/categories/tree/` | 200 OK, returns category hierarchy |
| 6 | Taxonomy tree | `curl "https://api.gastrotech.com/api/v1/taxonomy/tree/?series=600"` | 200 OK, returns taxonomy nodes |
| 7 | Products list | `curl https://api.gastrotech.com/api/v1/products/` | 200 OK, returns paginated products |
| 8 | Product detail | `curl https://api.gastrotech.com/api/v1/products/{slug}/` | 200 OK, returns product data |

### Media Endpoints

| # | Test | Command | Expected |
|---|------|---------|----------|
| 9 | Media metadata | `curl https://api.gastrotech.com/api/v1/media/{id}/` | 200 OK, returns media info |
| 10 | Media file | `curl -I https://api.gastrotech.com/api/v1/media/{id}/file/` | 200 OK, has ETag header |
| 11 | ETag caching | `curl -I -H "If-None-Match: \"<etag>\"" https://api.gastrotech.com/api/v1/media/{id}/file/` | 304 Not Modified |

### Authentication

| # | Test | Command | Expected |
|---|------|---------|----------|
| 12 | Login | `curl -X POST https://api.gastrotech.com/api/v1/auth/login/ -d '{"email":"admin@gastrotech.com","password":"..."}' -H "Content-Type: application/json"` | 200 OK, returns access + refresh tokens |
| 13 | Protected endpoint | `curl -H "Authorization: Bearer {token}" https://api.gastrotech.com/api/v1/auth/me/` | 200 OK, returns user info |

### Admin Endpoints (Requires Auth)

| # | Test | Command | Expected |
|---|------|---------|----------|
| 14 | Admin search | `curl -H "Authorization: Bearer {token}" "https://api.gastrotech.com/api/v1/admin/search/?q=test"` | 200 OK, returns search results |
| 15 | Admin stats | `curl -H "Authorization: Bearer {token}" https://api.gastrotech.com/api/v1/admin/stats/` | 200 OK, returns dashboard stats |
| 16 | Inquiries list | `curl -H "Authorization: Bearer {token}" https://api.gastrotech.com/api/v1/admin/inquiries/` | 200 OK, returns inquiries |

### Cart Endpoints

| # | Test | Command | Expected |
|---|------|---------|----------|
| 17 | Create cart token | `curl -X POST https://api.gastrotech.com/api/v1/cart/token/` | 201 Created, returns cart_token |
| 18 | Get cart | `curl -H "X-Cart-Token: {token}" https://api.gastrotech.com/api/v1/cart/` | 200 OK, returns cart |
| 19 | Add item | `curl -X POST -H "X-Cart-Token: {token}" -H "Content-Type: application/json" -d '{"variant_id":"{uuid}","quantity":1}' https://api.gastrotech.com/api/v1/cart/items/` | 201 Created (or 409 if stock issue) |
| 20 | Stock error | Add more than stock | 409 Conflict with `{"detail":"insufficient_stock",...}` |

### Inquiry Endpoints

| # | Test | Command | Expected |
|---|------|---------|----------|
| 21 | Create inquiry | `curl -X POST https://api.gastrotech.com/api/v1/inquiries/ -H "Content-Type: application/json" -d '{"full_name":"Test","email":"test@test.com","message":"Test"}'` | 201 Created |
| 22 | Quote validate | `curl -X POST https://api.gastrotech.com/api/v1/quote/validate/ -H "Content-Type: application/json" -d '{"items":[{"model_code":"GKO6010","qty":1}]}'` | 200 OK, returns validation result |

---

## Rollback Procedure

If issues are found:

1. **Restore previous image**
   ```bash
   docker compose -f docker-compose.prod.yml down
   docker compose -f docker-compose.prod.yml up -d --force-recreate
   ```

2. **Restore database (if migrations were applied)**
   ```bash
   # See docs/DEPLOYMENT.md for restore procedure
   ```

3. **Notify team and create incident report**

---

## Post-Deployment

- [ ] Monitor error rates in Sentry (if configured)
- [ ] Check response times in logs
- [ ] Verify backup job runs successfully
- [ ] Update release notes / changelog
- [ ] Notify stakeholders of deployment

---

## Environment Variables Reference

### Required for Production

```bash
DJANGO_SECRET_KEY=           # Strong random key
DJANGO_ALLOWED_HOSTS=        # Comma-separated domains
DATABASE_URL=                # PostgreSQL connection string
REDIS_URL=                   # Redis connection string
CORS_ALLOWED_ORIGINS=        # Comma-separated origins
CSRF_TRUSTED_ORIGINS=        # Comma-separated origins
```

### Optional

```bash
APP_VERSION=1.0.0
SECURE_SSL_REDIRECT=1
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
SENTRY_DSN=
EMAIL_HOST=
```

See `docs/DEPLOYMENT.md` for complete list.
