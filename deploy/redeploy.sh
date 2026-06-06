#!/bin/bash
# ============================================
# Quick Redeploy - Run after pulling new code
# Usage: sudo bash deploy/redeploy.sh
# ============================================

set -e

APP_USER="deploy"
APP_DIR="/home/$APP_USER/Interior_Design_Server"

cd $APP_DIR

echo "=== Installing dependencies ==="
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt --quiet

echo "=== Running migrations ==="
sudo -u $APP_USER DJANGO_ENV=production $APP_DIR/venv/bin/python manage.py migrate

echo "=== Collecting static files ==="
sudo -u $APP_USER DJANGO_ENV=production $APP_DIR/venv/bin/python manage.py collectstatic --noinput

echo "=== Restarting services ==="
systemctl restart gunicorn
systemctl restart celery

echo "=== Done! ==="
systemctl status gunicorn --no-pager | head -3
