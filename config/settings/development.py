"""
Development settings for AI Art Evaluation System.
"""
from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ['*']

# Use SQLite for development if PostgreSQL is not available
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
}

# CORS - allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Celery - use database backend for development if Redis not available
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=True, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug toolbar (optional)
try:
    import debug_toolbar  # noqa: F401
    INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405
    INTERNAL_IPS = ['127.0.0.1']
except ImportError:
    pass

# Django extensions (optional)
try:
    import django_extensions  # noqa: F401
    INSTALLED_APPS += ['django_extensions']  # noqa: F405
except ImportError:
    pass

# Throttle rates - more permissive in development
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {  # noqa: F405
    'anon': '1000/hour',
    'user': '5000/hour',
}
