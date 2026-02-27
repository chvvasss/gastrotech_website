#!/bin/bash
set -euo pipefail

# HOTFIX: Add /admin proxy to gastrotech.com.tr nginx config
# This fixes admin panel 404/500 by routing /admin traffic directly
# through nginx to port 3001, bypassing Next.js rewrites.
#
# Usage: ssh root@187.77.84.4 'bash -s' < hotfix-admin-nginx.sh
# OR:    ssh root@187.77.84.4 then paste this script

NGINX_FILE="/etc/nginx/sites-available/gastrotech.com.tr"

echo "=== Admin Panel Nginx Hotfix ==="

# Check if admin location already exists
if grep -q "location /admin" "$NGINX_FILE" 2>/dev/null; then
    echo "SKIP: /admin location block already exists in $NGINX_FILE"
    echo "If admin still doesn't work, check: curl -sI http://127.0.0.1:3001/admin/"
    exit 0
fi

# Backup current config
cp "$NGINX_FILE" "${NGINX_FILE}.bak.$(date +%Y%m%d%H%M%S)"
echo "Backed up current config"

# Insert /admin location block before the catch-all location /
# This sed finds the first "location / {" and inserts the admin block before it
sed -i '/location \/ {/i\
    # Admin panel - proxy directly to admin container\
    location /admin {\
        proxy_pass http://127.0.0.1:3001;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection '"'"'upgrade'"'"';\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_read_timeout 60s;\
        proxy_connect_timeout 10s;\
    }\
' "$NGINX_FILE"

echo "Added /admin location block"

# Test nginx config
if nginx -t 2>&1; then
    echo "Nginx config test: OK"
    systemctl reload nginx
    echo "Nginx reloaded successfully"
else
    echo "ERROR: Nginx config test failed!"
    echo "Restoring backup..."
    cp "${NGINX_FILE}.bak."* "$NGINX_FILE" 2>/dev/null
    systemctl reload nginx
    echo "Backup restored"
    exit 1
fi

# Verify
echo ""
echo "=== Verification ==="
echo -n "Admin container (port 3001): "
if curl -sf http://127.0.0.1:3001/admin/ > /dev/null 2>&1; then
    echo "OK"
else
    echo "FAIL - admin container might not be running"
    echo "Check: docker compose -f /opt/gastrotech/docker-compose.prod.yml logs frontend-admin"
fi

echo -n "Public site admin proxy: "
if curl -sf http://127.0.0.1:80/admin/ -H "Host: gastrotech.com.tr" > /dev/null 2>&1; then
    echo "OK"
else
    echo "FAIL (might need HTTPS)"
fi

echo ""
echo "=== Hotfix Applied ==="
echo "Try: https://gastrotech.com.tr/admin/"
echo "Also: https://admin.gastrotech.com.tr/admin/"
