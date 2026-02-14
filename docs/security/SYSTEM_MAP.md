# GASTROTECH SYSTEM MAP
## Security Audit - Repository Structure Analysis

**Generated:** 2026-01-24
**Auditor:** Principal Application Security Engineer

---

## 1. SYSTEM ARCHITECTURE OVERVIEW

```
                     [INTERNET]
                         |
                         v
+--------------------------------------------------+
|              REVERSE PROXY (Nginx)               |
|  - TLS termination                              |
|  - Rate limiting (10r/s API, 5r/m login)       |
|  - Security headers                            |
+--------------------------------------------------+
                    |        |
         +----------+        +----------+
         v                              v
+------------------+          +------------------+
|  PUBLIC NEXT.JS  |          |  ADMIN NEXT.JS   |
|  (Port 3001)     |          |  (Port 3000)     |
|  - B2C catalog   |          |  - Admin panel   |
|  - Cart/quotes   |          |  - /admin/*      |
|  - /api/* proxy  |          |  - JWT auth      |
+------------------+          +------------------+
         |                              |
         +----------+        +----------+
                    v        v
+--------------------------------------------------+
|           DJANGO REST API (Port 8000)            |
|  - JWT Authentication (SimpleJWT)               |
|  - RBAC (admin/editor roles)                   |
|  - Rate limiting (60/min anon, 300/min auth)   |
|  - API v1 (/api/v1/*)                          |
+--------------------------------------------------+
         |                    |                    |
         v                    v                    v
+---------------+    +---------------+    +---------------+
|  PostgreSQL   |    |    Redis      |    |   Media DB    |
|  (Port 5432)  |    |  (Port 6379)  |    |  (in Postgres)|
|  - Catalog    |    |  - Cache      |    |  - Images     |
|  - Orders     |    |  - Sessions   |    |  - PDFs       |
|  - Users      |    |  - Throttle   |    |  - Videos     |
+---------------+    +---------------+    +---------------+
```

---

## 2. COMPONENT INVENTORY

### 2.1 Backend (Django 5.1)

| Path | Purpose | Security Relevance |
|------|---------|-------------------|
| `backend/config/settings/base.py` | Base configuration | **CRITICAL** - Secret key, JWT config |
| `backend/config/settings/prod.py` | Production settings | **CRITICAL** - Security headers, HSTS |
| `backend/config/settings/dev.py` | Development settings | LOW - Dev only |
| `backend/apps/accounts/` | User auth & management | **HIGH** - Authentication |
| `backend/apps/api/permissions.py` | RBAC permissions | **HIGH** - Authorization |
| `backend/apps/catalog/` | Product catalog | MEDIUM - Public data |
| `backend/apps/orders/` | Cart & orders | MEDIUM - User data |
| `backend/apps/inquiries/` | Quote requests | MEDIUM - PII handling |
| `backend/apps/common/` | Shared utilities | LOW - Helper functions |
| `backend/apps/ops/` | Admin operations | **HIGH** - Admin actions |
| `backend/apps/blog/` | Blog content | LOW - Public content |

### 2.2 Frontend (Next.js 15.5)

| Path | Purpose | Security Relevance |
|------|---------|-------------------|
| `frontend/public/` | Public-facing site | MEDIUM - XSS vectors |
| `frontend/admin/` | Admin panel | **HIGH** - Token storage |
| `frontend/public/src/middleware.ts` | API proxy | **HIGH** - Request forwarding |
| `frontend/admin/src/lib/api/token-store.ts` | JWT storage | **CRITICAL** - Token handling |

### 2.3 Infrastructure

| Path | Purpose | Security Relevance |
|------|---------|-------------------|
| `backend/docker/web/Dockerfile.prod` | Production image | **HIGH** - Container security |
| `backend/docker/nginx/nginx.conf` | Reverse proxy | **HIGH** - Security headers |
| `backend/docker-compose.prod.yml` | Production stack | **CRITICAL** - Secrets handling |
| `backend/.github/workflows/ci.yml` | CI pipeline | MEDIUM - Security checks |

---

## 3. TRUST BOUNDARIES

```
+------------------------------------------------------------------+
|  TRUST BOUNDARY 1: PUBLIC INTERNET                               |
|  - Untrusted users                                                |
|  - Anonymous cart operations                                      |
|  - Public catalog browsing                                        |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|  TRUST BOUNDARY 2: AUTHENTICATED USERS                           |
|  - JWT token required                                             |
|  - Rate limited access                                            |
|  - Can merge carts, submit inquiries                             |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|  TRUST BOUNDARY 3: ADMIN/EDITOR USERS                            |
|  - IsAdminOrEditor permission                                     |
|  - Full CRUD on catalog                                           |
|  - Access to /api/v1/admin/* endpoints                           |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|  TRUST BOUNDARY 4: INTERNAL SERVICES                             |
|  - PostgreSQL (internal network only)                            |
|  - Redis (internal network only)                                 |
|  - No external exposure                                          |
+------------------------------------------------------------------+
```

---

## 4. DATA CLASSIFICATION

### 4.1 Sensitive Data Types

| Data Type | Location | Classification | Protection Required |
|-----------|----------|---------------|---------------------|
| User passwords | PostgreSQL | **CRITICAL** | Argon2 hashing (Django default) |
| JWT tokens | Frontend localStorage | **HIGH** | XSS protection, short lifetime |
| Email addresses | PostgreSQL, Inquiries | **HIGH** | Access control, no logging |
| Company names | Inquiries | MEDIUM | Access control |
| Product prices | PostgreSQL, Variants | LOW | Business logic only |
| Session tokens | Redis | **HIGH** | Secure cookies |
| API keys | .env files | **CRITICAL** | Environment variables |

### 4.2 PII Inventory

| Field | Model/Location | GDPR/KVKK Consideration |
|-------|---------------|------------------------|
| email | User, Inquiry | Requires consent, deletion capability |
| full_name | Inquiry | Requires consent |
| company | Inquiry | B2B context |
| phone | Inquiry | Optional field |
| ip_address | Cart, Logs | Anonymization recommended |

---

## 5. CRITICAL ENDPOINTS

### 5.1 Authentication Endpoints

| Endpoint | Method | Auth | Risk |
|----------|--------|------|------|
| `/api/v1/auth/login/` | POST | None | **HIGH** - Brute force target |
| `/api/v1/auth/refresh/` | POST | Refresh token | MEDIUM |
| `/api/v1/auth/me/` | GET | JWT | LOW |

### 5.2 Admin Endpoints (Require IsAdminOrEditor)

| Endpoint | Method | Purpose | Risk |
|----------|--------|---------|------|
| `/api/v1/admin/products/` | CRUD | Product management | **HIGH** |
| `/api/v1/admin/categories/` | CRUD | Category management | **HIGH** |
| `/api/v1/admin/inquiries/` | GET/PATCH | Inquiry management | **HIGH** - PII access |
| `/api/v1/admin/import/` | POST | Bulk import | **CRITICAL** - RCE potential |

### 5.3 Public Endpoints

| Endpoint | Method | Rate Limit | Risk |
|----------|--------|------------|------|
| `/api/v1/nav/` | GET | 60/min | LOW |
| `/api/v1/products/` | GET | 60/min | LOW |
| `/api/v1/inquiries/` | POST | 20/hour | MEDIUM - Spam |
| `/api/v1/cart/` | * | 60/min | MEDIUM |

---

## 6. ENVIRONMENT VARIABLES

### 6.1 Critical Variables (MUST be secured in production)

| Variable | Purpose | Default Risk |
|----------|---------|--------------|
| `DJANGO_SECRET_KEY` | Cryptographic signing | **CRITICAL** - Default is insecure |
| `DATABASE_URL` | PostgreSQL connection | **CRITICAL** - Contains credentials |
| `REDIS_URL` | Redis connection | **HIGH** |
| `SENTRY_DSN` | Error tracking | MEDIUM - Can leak data |

### 6.2 Security Configuration Variables

| Variable | Purpose | Recommended Value |
|----------|---------|-------------------|
| `DJANGO_DEBUG` | Debug mode | `0` in production |
| `SECURE_SSL_REDIRECT` | HTTPS enforcement | `1` in production |
| `DJANGO_ALLOWED_HOSTS` | Host validation | Explicit domain list |
| `CORS_ALLOWED_ORIGINS` | CORS whitelist | Explicit origin list |
| `CSRF_TRUSTED_ORIGINS` | CSRF protection | Same as ALLOWED_HOSTS with https:// |

---

## 7. EXTERNAL DEPENDENCIES

### 7.1 Python Dependencies (High-Risk)

| Package | Version | CVE Check Required |
|---------|---------|-------------------|
| Django | 5.1 | Yes |
| djangorestframework | 3.15 | Yes |
| djangorestframework-simplejwt | 5.3 | Yes |
| Pillow | 10.4 | Yes - Image processing |
| psycopg | 3.1 | Yes |
| gunicorn | 22.0 | Yes |

### 7.2 JavaScript Dependencies (High-Risk)

| Package | Version | CVE Check Required |
|---------|---------|-------------------|
| next | 15.5 | Yes |
| react | 19 | Yes |
| @tanstack/react-query | * | Yes |

---

## 8. NETWORK TOPOLOGY

### 8.1 Production Network

```
Internet ─────> Cloudflare/WAF (optional)
                      │
                      v
            ┌─────────────────┐
            │   Nginx:443     │  TLS termination
            └─────────────────┘
                      │
        ┌─────────────┼─────────────┐
        v             v             v
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ Public  │   │  Admin  │   │ Django  │
   │Next:3001│   │Next:3000│   │ :8000   │
   └─────────┘   └─────────┘   └─────────┘
                                    │
                      ┌─────────────┼─────────────┐
                      v             v             v
                 ┌─────────┐   ┌─────────┐   ┌─────────┐
                 │ Postgres│   │  Redis  │   │ (Media) │
                 │  :5432  │   │  :6379  │   │ in DB   │
                 └─────────┘   └─────────┘   └─────────┘
```

### 8.2 Port Exposure

| Service | Internal Port | External Port | Exposure |
|---------|--------------|---------------|----------|
| Nginx | 80, 443 | 80, 443 | Public |
| Django | 8000 | - | Internal only |
| PostgreSQL | 5432 | - | Internal only |
| Redis | 6379 | - | Internal only |
| Public Next.js | 3001 | - | Via Nginx |
| Admin Next.js | 3000 | - | Via Nginx |

---

## 9. BACKUP & RECOVERY

### 9.1 Data Stores Requiring Backup

| Store | Data | Backup Method | Frequency |
|-------|------|---------------|-----------|
| PostgreSQL | All application data | pg_dump | Daily |
| Redis | Session/cache (ephemeral) | Optional | N/A |
| Media (in PostgreSQL) | Images, PDFs | Included in pg_dump | Daily |

### 9.2 Recovery Point Objective (RPO)

- **Target:** 24 hours
- **Media files:** Included in database backup
- **Configuration:** Git versioned

---

## 10. AUDIT TRAIL

### 10.1 Logging Configuration

| Log Type | Location | Retention | PII Handling |
|----------|----------|-----------|--------------|
| Django requests | stdout/stderr | Container logs | Request IDs only |
| Nginx access | /var/log/nginx/access.log | 30 days | IP anonymization recommended |
| Auth events | Django logs | 90 days | Email hashing recommended |
| Error tracking | Sentry (if configured) | 30 days | PII scrubbing required |

### 10.2 Audit Events to Track

- User login/logout
- Admin CRUD operations
- Inquiry submissions
- Failed authentication attempts
- Permission denials
- Import operations

---

**Next Steps:** Proceed to RISK_REGISTER.md for threat model and vulnerability findings.
