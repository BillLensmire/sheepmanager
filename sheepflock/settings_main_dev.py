"""
Demo settings for the upick Manager application.
"""
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database
# Use SQLite in production
DATABASES['default'] = DATABASES['main']
