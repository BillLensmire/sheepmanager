"""
Production settings for the Sheep Manager application.
"""

from .settings import *
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'default-key-replace-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Add your domain name(s) here
ALLOWED_HOSTS = ['sheep.exnihil.net']

# Database
# Use SQLite in production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DB_NAME', str(BASE_DIR / 'production.db.sqlite3')),
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

