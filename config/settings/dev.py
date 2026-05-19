"""
Development settings.
Usage: DJANGO_SETTINGS_MODULE=config.settings.dev
"""

from .base import *  

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = True

ALLOWED_HOSTS = ['*']

# ---------------------------------------------------------------------------
# CORS — allow all origins in development
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True

# ---------------------------------------------------------------------------
# Debug Toolbar (optional — install django-debug-toolbar from requirements/dev.txt)
# ---------------------------------------------------------------------------
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
# INTERNAL_IPS = ['127.0.0.1']

# ---------------------------------------------------------------------------
# Email — use console backend during development
# ---------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
