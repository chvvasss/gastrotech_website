#!/bin/bash
set -euo pipefail

# Gastrotech VPS Update Script
# Run this on the VPS to deploy a new version
# Usage: bash /opt/gastrotech/repo/vps-deploy/update.sh

DEPLOY_DIR="/opt/gastrotech"
REPO_DIR="$DEPLOY_DIR/repo"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.prod.yml"

echo "============================================"
echo "  Gastrotech - Deploy Update"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

# 1. Pull latest code
echo ""
echo "[1/7] Pulling latest code..."
cd "$REPO_DIR"
git fetch origin main
git reset --hard origin/main
echo "  OK - Code updated to $(git rev-parse --short HEAD)"

# 2. Copy docker-compose (always update)
echo ""
echo "[2/7] Updating docker-compose.prod.yml..."
cp "$REPO_DIR/vps-deploy/docker-compose.prod.yml" "$DEPLOY_DIR/docker-compose.prod.yml"
echo "  OK"

# 3. Update .env.prod - merge new vars without overwriting existing
echo ""
echo "[3/7] Checking .env.prod for new variables..."
if [ -f "$DEPLOY_DIR/.env.prod" ]; then
    # Add any new variables from template that don't exist yet
    while IFS= read -r line; do
        # Skip comments and empty lines
        [[ "$line" =~ ^#.*$ ]] && continue
        [[ -z "$line" ]] && continue
        # Extract variable name
        var_name=$(echo "$line" | cut -d'=' -f1)
        # If variable doesn't exist in current .env.prod, add it
        if ! grep -q "^${var_name}=" "$DEPLOY_DIR/.env.prod" 2>/dev/null; then
            echo "$line" >> "$DEPLOY_DIR/.env.prod"
            echo "  Added new var: $var_name"
        fi
    done < "$REPO_DIR/vps-deploy/.env.prod"
    echo "  OK - Existing .env.prod preserved"
else
    cp "$REPO_DIR/vps-deploy/.env.prod" "$DEPLOY_DIR/.env.prod"
    echo "  WARNING: Created new .env.prod - check secrets!"
fi

# 4. Update nginx configs (PRESERVE certbot SSL modifications)
echo ""
echo "[4/7] Updating nginx configs (preserving SSL)..."
for conf in gastrotech.com.tr api.gastrotech.com.tr admin.gastrotech.com.tr; do
    NGINX_FILE="/etc/nginx/sites-available/$conf"
    REPO_FILE="$REPO_DIR/vps-deploy/nginx/$conf"

    if [ -f "$NGINX_FILE" ]; then
        # Check if certbot has modified the file (has ssl_certificate directive)
        if grep -q "ssl_certificate" "$NGINX_FILE" 2>/dev/null; then
            echo "  $conf - SSL config detected, preserving certbot changes"
            # Only update the proxy_pass and location blocks, not SSL
            # Don't overwrite - certbot SSL config is precious
            continue
        fi
    fi

    # No SSL config found - safe to copy
    cp "$REPO_FILE" "$NGINX_FILE"
    echo "  $conf - Updated (no SSL yet)"
done

# Ensure symlinks exist
ln -sf /etc/nginx/sites-available/gastrotech.com.tr /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/api.gastrotech.com.tr /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/admin.gastrotech.com.tr /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t 2>/dev/null && echo "  Nginx config OK" || echo "  WARNING: Nginx config test failed!"

# 5. Stop old containers
echo ""
echo "[5/7] Stopping old containers..."
cd "$DEPLOY_DIR"
docker compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
echo "  OK"

# 6. Rebuild and start (NO CACHE - ensures fresh builds)
echo ""
echo "[6/7] Building Docker images (no cache)..."
docker compose -f "$COMPOSE_FILE" build --no-cache --parallel
echo "  OK - All images rebuilt"

echo ""
echo "[7/7] Starting services..."
docker compose -f "$COMPOSE_FILE" up -d --force-recreate
echo "  OK"

# 7. Wait and verify
echo ""
echo "Waiting for services to start..."
sleep 15

echo ""
echo "============================================"
echo "  Service Status"
echo "============================================"
docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Quick health check
echo ""
echo "Health checks:"
if curl -sf http://127.0.0.1:8000/api/v1/health/ > /dev/null 2>&1; then
    echo "  Backend API:      OK"
else
    echo "  Backend API:      FAIL - checking logs..."
    docker compose -f "$COMPOSE_FILE" logs --tail=20 backend
fi

if curl -sf http://127.0.0.1:3000/ > /dev/null 2>&1; then
    echo "  Frontend Public:  OK"
else
    echo "  Frontend Public:  FAIL"
fi

if curl -sf http://127.0.0.1:3001/admin/ > /dev/null 2>&1; then
    echo "  Frontend Admin:   OK"
else
    echo "  Frontend Admin:   FAIL"
fi

# Reload nginx
systemctl reload nginx 2>/dev/null && echo "  Nginx:            Reloaded" || echo "  Nginx:            Reload failed"

echo ""
echo "============================================"
echo "  Deploy complete!"
echo "  If SSL is not set up, run:"
echo "  certbot --nginx -d gastrotech.com.tr -d www.gastrotech.com.tr -d api.gastrotech.com.tr -d admin.gastrotech.com.tr"
echo "============================================"
