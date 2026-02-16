#!/bin/bash
set -euo pipefail

# Gastrotech VPS Setup Script (Offline Mode)
# Uses project_code.zip instead of git clone

echo "=== 🚀 Starting Gastrotech VPS Setup (Offline) ==="

# 1. Update System & Install Tools
echo "--- Updating System ---"
# apt-get update && apt-get upgrade -y  # Already run or safe to skip if run recently
apt-get install -y curl unzip ufw fail2ban

# 2. Firewall Setup
echo "--- Configuring Firewall ---"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 3. Docker Installation (Idempotent)
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

# 6. extract Code
echo "--- Extracting Code ---"
# Remove existing project code to ensure clean state
rm -rf /opt/gastrotech/backend /opt/gastrotech/frontend /opt/gastrotech/public /opt/gastrotech/package.json
mkdir -p /opt/gastrotech

if [ -f "/root/project_code.tar.gz" ]; then
    tar -xzf /root/project_code.tar.gz -C /opt/gastrotech/
else
    echo "ERROR: /root/project_code.zip not found!"
    exit 1
fi

# 7. Copy Config Files
echo "--- Copying Configuration ---"
# Paths are relative to /root/vps-deploy since uncommitted files are there
cp /root/vps-deploy/docker-compose.prod.yml /opt/gastrotech/docker-compose.prod.yml
cp /root/vps-deploy/nginx/* /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/gastrotech.com.tr /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/api.gastrotech.com.tr /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/admin.gastrotech.com.tr /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Copy Dockerfiles (since they are in vps-deploy, not in repo archive)
echo "--- Copying Dockerfiles ---"
cp /root/vps-deploy/frontend-public/Dockerfile /opt/gastrotech/frontend/public/Dockerfile
cp /root/vps-deploy/frontend-admin/Dockerfile /opt/gastrotech/frontend/admin/Dockerfile

# 8. Setup Environment
if [ ! -f "/opt/gastrotech/.env.prod" ]; then
    echo "--- Creating .env.prod ---"
    cp /root/vps-deploy/.env.prod /opt/gastrotech/.env.prod
    # Generate random secret key
    sed -i "s/__CHANGE_ME_TO_A_LONG_RANDOM_STRING__/$(openssl rand -hex 32)/g" /opt/gastrotech/.env.prod
    echo "NOTE: Default secrets used. Please update .env.prod manually later."
fi

# 9. Restore Backups (Media)
if [ -f "/root/media.tar.gz" ]; then
    echo "--- Restoring Media ---"
    # Move archive to backups first
    mv /root/media.tar.gz /opt/gastrotech/backups/
    # Extract into /opt/gastrotech/
    # tar will extract 'media/...' relative to -C
    tar -xzf /opt/gastrotech/backups/media.tar.gz -C /opt/gastrotech/
fi

# 10. Start Stack
echo "--- Starting Docker Stack ---"
cd /opt/gastrotech
# Provide context for build
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans

# 11. Database Restore
if [ -f "/root/gastrotech_final.dump" ]; then
    echo "--- Restoring Database (Waiting 15s for DB) ---"
    mv /root/gastrotech_final.dump /opt/gastrotech/backups/
    sleep 15
    
    # Create DB
    docker compose -f docker-compose.prod.yml exec -T db psql -U postgres -c "CREATE DATABASE gastrotech;" || true
    
    # Restore
    docker compose -f docker-compose.prod.yml exec -T db pg_restore -U postgres -d gastrotech --clean --if-exists /var/lib/postgresql/data/../../app/backups/gastrotech_final.dump || \
    # Using cat | docker exec is safer for paths
    cat /opt/gastrotech/backups/gastrotech_final.dump | docker compose -f docker-compose.prod.yml exec -T db pg_restore -U postgres -d gastrotech --clean --if-exists || true
    
    echo "--- Running Migrations ---"
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput
fi

# 12. Final Check
echo "--- Reloading Nginx ---"
nginx -t && systemctl reload nginx

echo "=== Setup Complete! ==="
