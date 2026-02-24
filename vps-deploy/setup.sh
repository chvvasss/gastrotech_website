#!/bin/bash
set -euo pipefail

# Gastrotech VPS Setup Script
# Run this on the VPS as root for FIRST TIME SETUP only
# For subsequent deploys, use: bash /opt/gastrotech/repo/vps-deploy/update.sh

echo "=== Gastrotech VPS Setup ==="

# 1. Update System
echo "--- Updating System ---"
apt-get update && apt-get upgrade -y
apt-get install -y curl git ufw fail2ban unzip

# 2. Firewall Setup
echo "--- Configuring Firewall ---"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 3. Docker Installation
if ! command -v docker &> /dev/null; then
    echo "--- Installing Docker ---"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# 4. Nginx & Certbot
echo "--- Installing Nginx & Certbot ---"
apt-get install -y nginx certbot python3-certbot-nginx

# 5. Project Directories
echo "--- Creating Project Directories ---"
mkdir -p /opt/gastrotech/backups
mkdir -p /opt/gastrotech/media
mkdir -p /opt/gastrotech/backend/staticfiles

# 6. Clone/Pull Repo
if [ -d "/opt/gastrotech/repo" ]; then
    echo "--- Pulling latest code ---"
    cd /opt/gastrotech/repo
    git pull origin main
else
    echo "--- Cloning Repo ---"
    git clone https://github.com/chvvasss/gastrotech_website.git /opt/gastrotech/repo
fi

# 7. Copy Config Files
echo "--- Copying Configuration ---"
cp /opt/gastrotech/repo/vps-deploy/docker-compose.prod.yml /opt/gastrotech/docker-compose.prod.yml

# Copy nginx configs (only if they don't exist yet - preserve certbot SSL)
for conf in gastrotech.com.tr api.gastrotech.com.tr admin.gastrotech.com.tr; do
    if [ ! -f "/etc/nginx/sites-available/$conf" ]; then
        cp "/opt/gastrotech/repo/vps-deploy/nginx/$conf" "/etc/nginx/sites-available/$conf"
        echo "  Created nginx config: $conf"
    else
        echo "  Nginx config exists, preserving: $conf"
    fi
done

ln -sf /etc/nginx/sites-available/gastrotech.com.tr /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/api.gastrotech.com.tr /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/admin.gastrotech.com.tr /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 8. Setup Environment
echo "--- Setting up .env.prod ---"
if [ ! -f "/opt/gastrotech/.env.prod" ]; then
    cp /opt/gastrotech/repo/vps-deploy/.env.prod /opt/gastrotech/.env.prod
    echo "  Created .env.prod from template"
    echo "  WARNING: Review and update secrets in /opt/gastrotech/.env.prod!"
else
    echo "  Using existing /opt/gastrotech/.env.prod"
fi

# 9. Restore Backups (if present)
if [ -f "/opt/gastrotech/backups/media.zip" ]; then
    echo "--- Restoring Media ---"
    unzip -o /opt/gastrotech/backups/media.zip -d /opt/gastrotech/
fi

# 10. Start Stack
echo "--- Cleaning up stale containers ---"
cd /opt/gastrotech
docker compose -f docker-compose.prod.yml down --remove-orphans || true
docker system prune -f

echo "--- Starting Docker Stack (Forced Rebuild) ---"
docker compose -f docker-compose.prod.yml build --no-cache --parallel
docker compose -f docker-compose.prod.yml up -d --force-recreate

# 11. Database Restore (if dump exists)
if [ -f "/opt/gastrotech/backups/gastrotech_final.dump" ]; then
    echo "--- Restoring Database (Waiting 15s for DB to be ready) ---"
    sleep 15
    docker compose -f docker-compose.prod.yml exec -T db psql -U gastrotech -c "SELECT 1;" 2>/dev/null || \
        echo "WARNING: Database not ready yet, you may need to run restore manually"

    cat /opt/gastrotech/backups/gastrotech_final.dump | \
        docker compose -f docker-compose.prod.yml exec -T db pg_restore -U gastrotech -d gastrotech --clean --if-exists 2>/dev/null || \
        echo "WARNING: DB restore had issues - check manually"

    echo "--- Running Migrations ---"
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput
fi

# 12. Nginx
echo "--- Checking Nginx Config ---"
nginx -t && systemctl reload nginx

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "NEXT STEPS:"
echo "1. Review /opt/gastrotech/.env.prod and update secrets"
echo "2. Set up SSL certificates:"
echo "   certbot --nginx -d gastrotech.com.tr -d www.gastrotech.com.tr -d api.gastrotech.com.tr -d admin.gastrotech.com.tr"
echo "3. After SSL is set up, update /opt/gastrotech/.env.prod:"
echo "   SECURE_SSL_REDIRECT=True"
echo "   SESSION_COOKIE_SECURE=True"
echo "   CSRF_COOKIE_SECURE=True"
echo "4. Restart backend: cd /opt/gastrotech && docker compose -f docker-compose.prod.yml restart backend"
echo ""
echo "For future updates, use: bash /opt/gastrotech/repo/vps-deploy/update.sh"
