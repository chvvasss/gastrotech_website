#!/bin/bash
set -euo pipefail

# Gastrotech VPS Setup Script
# Run this on the VPS as root

echo "=== 🚀 Starting Gastrotech VPS Setup ==="

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

# 6. Deployment Files
# Assuming this script is run from /opt/gastrotech/vpsc-deploy or similar
# We expect the repo content at /opt/gastrotech/repo

# 7. Clone/Pull Repo
if [ -d "/opt/gastrotech/repo" ]; then
    echo "--- Pulling latest code ---"
    cd /opt/gastrotech/repo
    git pull origin main
else
    echo "--- Cloning Repo ---"
    git clone https://github.com/chvvasss/gastrotech_website.git /opt/gastrotech/repo
fi

# 8. Copy Config Files
echo "--- Copying Configuration ---"
cp /opt/gastrotech/repo/vps-deploy/docker-compose.prod.yml /opt/gastrotech/docker-compose.prod.yml
cp /opt/gastrotech/repo/vps-deploy/nginx/* /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/gastrotech.com.tr /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/api.gastrotech.com.tr /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/admin.gastrotech.com.tr /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 9. Setup Environment
echo "--- Recreating .env.prod from template ---"
cp -f /opt/gastrotech/repo/vps-deploy/.env.prod /opt/gastrotech/.env.prod
echo "WARNING: Please edit /opt/gastrotech/.env.prod and set secrets!"

# Ensure Internal Docker Network URLs are used instead of localhost
echo "--- Fixing internal network URLs in .env.prod ---"
sed -i 's|http://127.0.0.1:8000|http://backend:8000|g' /opt/gastrotech/.env.prod
sed -i 's|http://127.0.0.1:3001|http://frontend-admin:3001|g' /opt/gastrotech/.env.prod

# 10. Restore Backups (if present)
if [ -f "/opt/gastrotech/backups/media.zip" ]; then
    echo "--- Restoring Media ---"
    unzip -o /opt/gastrotech/backups/media.zip -d /opt/gastrotech/
    # If zip contains 'media' folder, it might double nest. Ensure contents are in /opt/gastrotech/media
    # Assuming backups/media.zip contains 'media/...'
fi

# 11. Start Stack
echo "--- Cleaning up stale containers and Next.js cache ---"
cd /opt/gastrotech
docker compose -f docker-compose.prod.yml down --remove-orphans || true
docker system prune -f

echo "--- Starting Docker Stack (Forced Rebuild) ---"
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d --force-recreate

# 12. Database Restore (if dump exists)
if [ -f "/opt/gastrotech/backups/gastrotech_final.dump" ]; then
    echo "--- Restoring Database (Waiting 10s for DB to be ready) ---"
    sleep 10
    # Create DB if not exists
    docker compose -f docker-compose.prod.yml exec -T db psql -U postgres -c "CREATE DATABASE gastrotech;" || true
    # Restore
    docker compose -f docker-compose.prod.yml exec -T db pg_restore -U postgres -d gastrotech --clean --if-exists /opt/gastrotech/app/backups/gastrotech_final.dump || \
    # If the file is on host, we need to copy it into container or mount valid volume
    # easier: cat dump | docker exec ...
    cat /opt/gastrotech/backups/gastrotech_final.dump | docker compose -f docker-compose.prod.yml exec -T db pg_restore -U postgres -d gastrotech --clean --if-exists
    
    echo "--- Running Migrations ---"
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput
fi

# 13. SSL Setup (Interactive - run manually if needed)
echo "--- Checking Nginx Config ---"
nginx -t && systemctl reload nginx

echo "=== Setup Complete! ==="
echo "If DNS is ready, run: certbot --nginx -d gastrotech.com.tr -d www.gastrotech.com.tr -d api.gastrotech.com.tr -d admin.gastrotech.com.tr"
