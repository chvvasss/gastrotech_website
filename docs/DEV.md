# GastroTech Development Guide

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- PowerShell (Windows) or Bash (Linux/Mac)

### Start Backend (Docker)

```bash
cd backend
docker compose up -d --build
```

Backend will be available at `http://localhost:8000`

### Start Frontend (Admin Panel)

```bash
cd frontend/admin
npm install
npm run dev
```

Admin panel will be available at `http://localhost:3000`

---

## Docker Container Management

### Clean Start (Recommended)

If you're having container conflicts or want a fresh start:

```bash
cd backend

# Stop and remove all project containers + orphans
docker compose down --remove-orphans

# Start fresh
docker compose up -d --build
```

### One-Time Cleanup for Legacy Containers

If you see errors about containers named `gastrotech_db` or `gastrotech_redis`:

```powershell
# PowerShell - Remove legacy named containers
docker rm -f gastrotech_db gastrotech_redis gastrotech_web 2>$null

# Then restart
cd backend
docker compose down --remove-orphans
docker compose up -d --build
```

```bash
# Bash - Remove legacy named containers  
docker rm -f gastrotech_db gastrotech_redis gastrotech_web 2>/dev/null

# Then restart
cd backend
docker compose down --remove-orphans
docker compose up -d --build
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f db
docker compose logs -f redis
```

### Execute Commands in Container

```bash
# Django management commands
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py ensure_dev_admin

# Database shell
docker compose exec db psql -U postgres -d gastrotech

# Redis CLI
docker compose exec redis redis-cli
```

### Volume Management

The project uses named volumes to persist data:

| Volume Name | Purpose |
|-------------|---------|
| `gastrotechcom_cursor_postgres_data` | PostgreSQL database |
| `gastrotechcom_cursor_redis_data` | Redis cache |
| `gastrotechcom_cursor_static_volume` | Django static files |
| `gastrotechcom_cursor_media_volume` | Uploaded media files |

To completely reset data:

```bash
docker compose down -v  # Removes containers AND volumes
docker compose up -d --build
```

---

## Default Dev Credentials

The backend automatically creates a dev admin user on startup (only in dev mode):

- **Email:** `admin@gastrotech.com`
- **Password:** `admin123`

This is handled by the `ensure_dev_admin` management command which runs automatically in the Docker entrypoint when `DEBUG=True` or `DJANGO_ENV=dev`.

---

## PowerShell API Testing

> **IMPORTANT:** In PowerShell, `curl` is an alias for `Invoke-WebRequest`. 
> Use `curl.exe` for real curl or use `Invoke-RestMethod`.

### Test Backend Health

Using curl.exe:
```powershell
curl.exe -i "http://localhost:8000/api/v1/health/"
```

Using PowerShell native:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health/"
```

### Test Login

Using curl.exe:
```powershell
curl.exe -i -X POST "http://localhost:8000/api/v1/auth/login/" `
  -H "Content-Type: application/json" `
  -d "{`"email`":`"admin@gastrotech.com`",`"password`":`"admin123`"}"
```

Using PowerShell native (recommended):
```powershell
$body = @{
    email = "admin@gastrotech.com"
    password = "admin123"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/auth/login/" `
  -ContentType "application/json" `
  -Body $body
```

Expected response:
```json
{
    "access": "eyJ...",
    "refresh": "eyJ..."
}
```

### Test Authenticated Endpoint

```powershell
# First, get token
$loginResponse = Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/auth/login/" `
  -ContentType "application/json" `
  -Body (@{ email="admin@gastrotech.com"; password="admin123" } | ConvertTo-Json)

$token = $loginResponse.access

# Use token for authenticated request
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/me/" `
  -Headers @{ Authorization = "Bearer $token" }
```

---

## Backend Management Commands

### Ensure Dev Admin Exists

```bash
# Via Docker
docker compose exec web python manage.py ensure_dev_admin

# Locally
python manage.py ensure_dev_admin
```

### Run Migrations

```bash
docker compose exec web python manage.py migrate
```

### Create Superuser Manually

```bash
docker compose exec web python manage.py createsuperuser
```

### Run Tests

```bash
docker compose exec web python manage.py test
```

---

## Troubleshooting

### Container Name Conflicts

If you see errors like:
```
Error: container name "/gastrotech_db" is already in use
```

This means old containers with hardcoded names exist. Fix:

```powershell
# Remove old named containers
docker rm -f gastrotech_db gastrotech_redis gastrotech_web

# Restart
docker compose down --remove-orphans
docker compose up -d --build
```

### Port Already in Use

If port 8000, 5432, or 6379 is already in use:

```powershell
# Find what's using the port (example: 8000)
netstat -ano | findstr :8000

# Or use Docker to check
docker ps
```

Stop the conflicting service or change ports in docker-compose.yml.

### Login Returns 401

1. **Check backend is running:**
   ```powershell
   curl.exe -i "http://localhost:8000/api/v1/health/"
   ```

2. **Check dev admin exists:**
   ```bash
   docker compose exec web python manage.py ensure_dev_admin
   ```

3. **Check credentials:** Use exactly `admin@gastrotech.com` / `admin123`

4. **Clear browser localStorage:** Old tokens can cause issues

5. **Check frontend console:** Look for debug logs showing if Authorization header is attached

### Frontend Shows "Backend Unreachable"

1. Check Docker is running: `docker ps`
2. Check backend logs: `docker compose logs web`
3. Verify NEXT_PUBLIC_BACKEND_URL in frontend env

### Token Contamination

If login fails with 401 despite correct credentials, the frontend may be sending stale Authorization header.

The fix (already implemented):
- Frontend clears tokens before login attempt
- Public paths (/auth/login/, /auth/refresh/) never get Authorization header

### Database Connection Issues

If Django can't connect to the database:

1. Check db container is healthy:
   ```bash
   docker compose ps
   ```

2. Check db logs:
   ```bash
   docker compose logs db
   ```

3. Verify DATABASE_URL uses service name `db` (not `localhost` or IP):
   ```
   DATABASE_URL=postgres://postgres:postgres@db:5432/gastrotech
   ```

---

## API URL Convention

All API URLs use **trailing slashes** for DRF compatibility:

✅ Correct:
- `/api/v1/auth/login/`
- `/api/v1/products/`
- `/api/v1/admin/products/`

❌ Wrong:
- `/api/v1/auth/login`
- `/api/v1/products`

---

## Environment Variables

### Backend (docker-compose.yml or .env)

The docker-compose.yml sets these automatically:
```env
DEBUG=True
DJANGO_ENV=dev
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=postgres://postgres:postgres@db:5432/gastrotech
REDIS_URL=redis://redis:6379/0
```

### Frontend (frontend/admin/.env.local)

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

---

## Service DNS Names

Docker Compose creates an internal network where services can reach each other by name:

| Service | Internal DNS | External Port |
|---------|--------------|---------------|
| db | `db:5432` | `localhost:5432` |
| redis | `redis:6379` | `localhost:6379` |
| web | `web:8000` | `localhost:8000` |

Django uses `db` and `redis` as hostnames in DATABASE_URL and REDIS_URL.
Do NOT use `localhost` or container names in these URLs.
