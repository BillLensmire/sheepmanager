# Sheep Manager Deployment Guide

This guide provides instructions for deploying the Sheep Manager application on a Linux server like Linode.

## Prerequisites

- A Linux server (Ubuntu 22.04 LTS recommended)
- A domain name pointing to your server
- Basic knowledge of Linux command line
- SSH access to your server

## Server Setup

### 1. Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Required Packages

```bash
# using postgress ...
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib certbot python3-certbot-nginx
# without postgress ... (ie sqlite3)
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx
```

## Application Deployment

### 1. Create Application Directory

```bash
sudo mkdir -p /var/www/sheepmanager
sudo chown -R www-data:www-data /var/www/sheepmanager
```

### 2. Clone the Repository (or Transfer Files)

Option 1: Clone from Git (if using version control):
```bash
git clone https://github.com/BillLensmire/sheepmanager.git /var/www/sheepmanager
```

Option 2: Transfer files using SCP (from your local machine):
```bash
scp -r /path/to/local/sheepmanager/* user@your-server:/var/www/sheepmanager/
```

sudo chown -R www-data:www-data /var/www/sheepmanager

### 3. Set Up Virtual Environment

```bash
cd /var/www/sheepmanager
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

# Skip if not using progreSQL

### 4. Set Up PostgreSQL Database

```bash
sudo -u postgres psql
```

In the PostgreSQL prompt:
```sql
CREATE DATABASE sheepmanager;
CREATE USER sheepmanager_user WITH PASSWORD 'your-secure-password';
ALTER ROLE sheepmanager_user SET client_encoding TO 'utf8';
ALTER ROLE sheepmanager_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE sheepmanager_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE sheepmanager TO sheepmanager_user;
\q
```

### 5. Configure Environment Variables

Create a `.env` file:
```bash
sudo nano /var/www/sheepmanager/.env
```

Add the following content for postgreSQL
```
DJANGO_SETTINGS_MODULE=sheepflock.settings_production
DJANGO_SECRET_KEY=your-very-secure-secret-key
DB_NAME=sheepmanager
DB_USER=sheepmanager_user
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432
Debug=False
```


Add the following content for sqlite3
```
DJANGO_SETTINGS_MODULE=sheepflock.settings_production
DJANGO_SECRET_KEY=your-very-secure-secret-key
DB_NAME=sheepmanager.sqlite3
DEBUG=False
```

Load environment variables in systemd service:
```bash
sudo nano /etc/systemd/system/sheepmanager.service
```

Copy the content from the `sheepmanager.service` file in your project.

### 6. Configure Production Settings

The project includes a `sheepflock.settings_production.py` file that inherits from the base settings and applies production-specific configurations. You need to modify this file based on your database choice:

#### For PostgreSQL:

The default `sheepflock.settings_production.py` is already configured for PostgreSQL. Make sure it contains:

```python
from .settings import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'default-key-replace-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Add your domain name(s) here
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# Database
# Use PostgreSQL in production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'sheepmanager'),
        'USER': os.environ.get('DB_USER', 'sheepmanager_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Static and media files
STATIC_ROOT = '/var/www/sheepmanager/staticfiles'
MEDIA_ROOT = '/var/www/sheepmanager/media'

# Add missing import
import os
```

#### For SQLite3:

If you're using SQLite3, modify the `settings_production.py` file to use SQLite instead of PostgreSQL:

```python
from .settings import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'default-key-replace-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Add your domain name(s) here
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# Database
# Use SQLite in production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DB_NAME', str(BASE_DIR / 'sheepmanager.sqlite3')),
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Static and media files
STATIC_ROOT = '/var/www/sheepmanager/staticfiles'
MEDIA_ROOT = '/var/www/sheepmanager/media'

# Add missing import
import os
```

Update the domain names in `ALLOWED_HOSTS` to match your actual domain.

### 7. Set Up Django Application

```bash
cd /var/www/sheepmanager
source .venv/bin/activate

# Apply migrations
python3 manage.py migrate --settings=sheepflock.settings_production

# Collect static files
python3 manage.py collectstatic --settings=sheepflock.settings_production --no-input

# Create superuser
python3 manage.py createsuperuser --settings=sheepflock.settings_production
```

sudo chown -R www-data:www-data /var/www/sheepmanager

### 8. Set Up Gunicorn

Create required directories:
```bash
sudo mkdir -p /run/gunicorn
sudo mkdir -p /var/log/gunicorn
sudo chown -R www-data:www-data /run/gunicorn /var/log/gunicorn
```

Copy the systemd service file:
```bash
sudo cp /var/www/sheepmanager/sheepmanager.service /etc/systemd/system/
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sheepmanager
sudo systemctl start sheepmanager
```

Check status:
```bash
sudo systemctl status sheepmanager
```

### 9. Set Up Nginx

Copy the Nginx configuration:
```bash
sudo cp /var/www/sheepmanager/sheepmanager_nginx.conf /etc/nginx/sites-available/sheepmanager
```

Edit the configuration to update your domain name:
```bash
sudo nano /etc/nginx/sites-available/sheepmanager
```

Create a symbolic link:
```bash
sudo ln -s /etc/nginx/sites-available/sheepmanager /etc/nginx/sites-enabled/
```

Test Nginx configuration:
```bash
sudo nginx -t
```

Restart Nginx:
```bash
sudo systemctl restart nginx
```

sudo ufw allow 'Nginx Full'
sudo ufw delete allow 'Nginx HTTP'


### 10. Set Up SSL with Let's Encrypt

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Follow the prompts to complete the SSL setup.

### 11. Final Checks

- Visit your domain in a web browser to ensure the application is running
- Try logging in to the admin interface at `https://your-domain.com/admin/`
- Check the logs if there are any issues:
  ```bash
  sudo journalctl -u sheepmanager
  sudo cat /var/log/gunicorn/sheepmanager-error.log
  sudo cat /var/log/nginx/sheepmanager-error.log
  ```

## Maintenance

### Updating the Application

```bash
cd /var/www/sheepmanager
git pull  # If using git

source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --settings=sheepflock.settings_production
python manage.py collectstatic --settings=sheepflock.settings_production --no-input

sudo systemctl restart sheepmanager
```

### Backing Up the Database

```bash
sudo -u postgres pg_dump sheepmanager > sheepmanager_backup_$(date +%Y%m%d).sql
```

### Renewing SSL Certificates

SSL certificates from Let's Encrypt are valid for 90 days and are automatically renewed by a cron job. You can manually renew them with:

```bash
sudo certbot renew
```

## Troubleshooting

### 1. Application Not Loading

Check Gunicorn status:
```bash
sudo systemctl status sheepmanager
```

Check Gunicorn logs:
```bash
sudo cat /var/log/gunicorn/sheepmanager-error.log
```

### 2. Database Connection Issues

Verify PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

Check database connection settings in the `.env` file.

### 3. Static Files Not Loading

Ensure static files were collected:
```bash
source .venv/bin/activate
python manage.py collectstatic --settings=sheepflock.settings_production --no-input
```

Check Nginx configuration for the static files location.

### 4. Permission Issues

Ensure proper ownership of files:
```bash
sudo chown -R www-data:www-data /var/www/sheepmanager/media
sudo chown -R www-data:www-data /var/www/sheepmanager/staticfiles
```
