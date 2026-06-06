#!/bin/bash
# ============================================
# App Setup - Run after project files are on server
# Run as root: sudo bash deploy/setup_app.sh
# ============================================

set -e

APP_USER="deploy"
APP_DIR="/home/$APP_USER/Interior_Design_Server"

echo "=== 1. Setup Python Virtual Environment ==="
cd $APP_DIR
sudo -u $APP_USER python3.12 -m venv venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt

echo "=== 2. Run Migrations ==="
sudo -u $APP_USER DJANGO_ENV=production $APP_DIR/venv/bin/python manage.py migrate

echo "=== 3. Collect Static Files ==="
sudo -u $APP_USER DJANGO_ENV=production $APP_DIR/venv/bin/python manage.py collectstatic --noinput

echo "=== 4. Seed Data ==="
sudo -u $APP_USER DJANGO_ENV=production $APP_DIR/venv/bin/python manage.py seed_data

echo "=== 5. Create Superuser ==="
sudo -u $APP_USER DJANGO_ENV=production $APP_DIR/venv/bin/python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@admin.com').exists():
    User.objects.create_superuser('admin', 'admin@admin.com', 'admin123')
    print('Superuser created: admin@admin.com / admin123')
else:
    print('Superuser already exists')
"

echo "=== 6. Setup Media Directory ==="
mkdir -p $APP_DIR/media/uploads/rooms $APP_DIR/media/generated
chown -R $APP_USER:www-data $APP_DIR/media
chmod -R 775 $APP_DIR/media

echo "=== 7. Setup Log Directory ==="
mkdir -p /var/log/gunicorn
chown $APP_USER:www-data /var/log/gunicorn

echo "=== 8. Install Systemd Services ==="
cp $APP_DIR/deploy/gunicorn.service /etc/systemd/system/gunicorn.service
cp $APP_DIR/deploy/celery.service /etc/systemd/system/celery.service
systemctl daemon-reload
systemctl enable gunicorn celery
systemctl start gunicorn celery

echo "=== 9. Setup Nginx ==="
cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/roomai
ln -sf /etc/nginx/sites-available/roomai /etc/nginx/sites-enabled/roomai
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "=== APP SETUP COMPLETE ==="
echo ""
echo "Services status:"
systemctl status gunicorn --no-pager -l | head -5
systemctl status celery --no-pager -l | head -5
echo ""
echo "Next steps:"
echo "  1. Update DOMAIN in deploy/nginx.conf"
echo "  2. Run: sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com"
echo "  3. Set SECURE_SSL_REDIRECT=True in .env"
echo "  4. Run: sudo systemctl restart gunicorn"
