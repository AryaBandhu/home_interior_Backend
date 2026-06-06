#!/bin/bash
# ============================================
# Hostinger Ubuntu VPS - Full Setup Script
# Run as root: sudo bash deploy/setup_server.sh
# ============================================

set -e

APP_USER="deploy"
APP_DIR="/home/$APP_USER/Interior_Design_Server"
DOMAIN="yourdomain.com"  # <-- CHANGE THIS

echo "=== 1. System Update ==="
apt update && apt upgrade -y

echo "=== 2. Install Dependencies ==="
apt install -y python3.12 python3.12-venv python3.12-dev \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    certbot python3-certbot-nginx \
    git curl ufw

echo "=== 3. Create Deploy User ==="
if ! id "$APP_USER" &>/dev/null; then
    adduser --disabled-password --gecos "" $APP_USER
    usermod -aG www-data $APP_USER
fi

echo "=== 4. Configure Firewall ==="
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "=== 5. Setup PostgreSQL ==="
sudo -u postgres psql -c "CREATE DATABASE roomai;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER roomai_user WITH PASSWORD 'CHANGE_ME_STRONG_PASSWORD';" 2>/dev/null || true
sudo -u postgres psql -c "ALTER ROLE roomai_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE roomai_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE roomai_user SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE roomai TO roomai_user;"

echo "=== 6. Setup App Directory ==="
mkdir -p $APP_DIR
chown $APP_USER:www-data $APP_DIR

echo "=== 7. Clone/Copy Project ==="
echo ">> Copy your project files to $APP_DIR"
echo ">> Then run: sudo bash deploy/setup_app.sh"

echo ""
echo "=== SERVER SETUP COMPLETE ==="
echo "Next steps:"
echo "  1. Copy project to $APP_DIR"
echo "  2. Copy .env.prod to $APP_DIR/.env and fill in real values"
echo "  3. Run: sudo bash $APP_DIR/deploy/setup_app.sh"
