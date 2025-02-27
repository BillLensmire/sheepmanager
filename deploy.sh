#!/bin/bash
# Deployment script for Sheep Manager application

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

echo "===== Sheep Manager Deployment Script ====="
echo "This script will deploy the Sheep Manager application."
echo "Make sure you have updated the domain name in the configuration files."

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p /var/www/sheepmanager
mkdir -p /run/gunicorn
mkdir -p /var/log/gunicorn
chown -R www-data:www-data /run/gunicorn /var/log/gunicorn

# Copy application files
echo "Copying application files..."
rsync -av --exclude='.git' --exclude='.venv' --exclude='__pycache__' \
      --exclude='*.pyc' --exclude='*.pyo' --exclude='*.pyd' \
      /path/to/sheepmanager/ /var/www/sheepmanager/

# Set permissions
echo "Setting permissions..."
chown -R www-data:www-data /var/www/sheepmanager

# Set up virtual environment
echo "Setting up virtual environment..."
cd /var/www/sheepmanager
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set up systemd service
echo "Setting up systemd service..."
cp /var/www/sheepmanager/sheepmanager.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable sheepmanager
systemctl start sheepmanager

# Set up Nginx
echo "Setting up Nginx..."
cp /var/www/sheepmanager/sheepmanager_nginx.conf /etc/nginx/sites-available/sheepmanager
ln -sf /etc/nginx/sites-available/sheepmanager /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

echo "===== Deployment Complete ====="
echo "Next steps:"
echo "1. Update the domain name in /etc/nginx/sites-available/sheepmanager"
echo "2. Set up SSL with: certbot --nginx -d your-domain.com -d www.your-domain.com"
echo "3. Create a superuser with: cd /var/www/sheepmanager && source .venv/bin/activate && python manage.py createsuperuser --settings=sheepflock.settings_production"
