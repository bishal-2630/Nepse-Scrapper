"""
Django settings for nepse_scraper project.
Optimized for Android Termux deployment with ngrok public access.
"""

import os
from pathlib import Path
from datetime import time
import dj_database_url
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== SECURITY ====================
# WARNING: For production, use environment variables!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-mobile-android-nepse-server-2024-key')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'  # Keep True for debugging on mobile

# Android mobile specific - allow all for ngrok and local network
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '10.0.2.2',  # Android emulator
    '*.ngrok.io',  # Allow all ngrok subdomains
    '*.ngrok-free.app',  # ngrok free domain
    '*.serveo.net',  # Serveo domain
    '*.loca.lt',  # LocalTunnel domain
    '*.onrender.com',
    '*.trycloudflare.com',  # Render domain (if using)
    '*',  # Allow all for simplicity - RESTRICT IN PRODUCTION!
]

# CORS - Allow all for API access
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "https://*.ngrok.io",
    "https://*.ngrok-free.app",
    "https://*.trycloudflare.com",
    "http://*.trycloudflare.com",
    "https://niagara-los-protocols-cottage.trycloudflare.com",
    "http://niagara-los-protocols-cottage.trycloudflare.com",
]

# CSRF trusted origins for POST requests from ngrok
CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok.io',
    'https://*.ngrok-free.app',
    'https://*.serveo.net',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.trycloudflare.com',
    'https://niagara-los-protocols-cottage.trycloudflare.com',
]

# ==================== APPLICATION DEFINITION ====================
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps (LIGHTWEIGHT for mobile)
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    
    # Local apps
    'scrapers',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # MUST BE FIRST or at least before CommonMiddleware
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'nepse_scraper.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'nepse_scraper.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,  # Increase timeout for mobile
        }
    }
}



# Simplified for mobile API server
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4,  # Shorter for mobile convenience
        }
    },
]

# ==================== INTERNATIONALIZATION ====================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'  # Nepal time
USE_I18N = True
USE_TZ = True

# ==================== STATIC FILES ====================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Additional static directories
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# ==================== DEFAULT PRIMARY KEY ====================
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# ==================== REST FRAMEWORK ====================
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow public API access
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,  # Larger page size for mobile efficiency
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # Limit anonymous requests
        'user': '1000/hour'
    }
}

# ==================== CELERY CONFIGURATION ====================
# Optimized for Android mobile (low memory usage)
CELERY_BROKER_URL = 'redis://localhost:6379/0' if os.environ.get('USE_REDIS') else 'memory://'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kathmandu'

# Mobile-optimized Celery settings
CELERY_WORKER_CONCURRENCY = 1  # Single worker to save memory
CELERY_WORKER_MAX_TASKS_PER_CHILD = 10  # Restart worker after 10 tasks
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes max per task
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes soft limit

# Celery Beat schedule (optimized for mobile battery)
CELERY_BEAT_SCHEDULE = {
    # Scrape during market hours only (to save battery/data)
    'scrape-market-hours': {
        'task': 'scrapers.tasks.scrape_24x7',
        'schedule': 300,  # Every 5 minutes
        'options': {
            'expires': 120,  # Expire after 2 minutes if not picked up
        }
    },
    
    # Daily maintenance at 4 PM Nepal time
    'daily-maintenance': {
        'task': 'scrapers.tasks.daily_maintenance',
        'schedule': 86400,  # Once per day
    },
}

# ==================== MARKET CONFIGURATION ====================
# Nepal stock market hours (Sunday-Thursday)
MARKET_OPEN_HOUR = 11
MARKET_CLOSE_HOUR = 15
MARKET_OPEN_TIME = time(11, 0)  # 11:00 AM
MARKET_CLOSE_TIME = time(15, 0)  # 3:00 PM

# Trading days (0=Monday, 6=Sunday)
TRADING_DAYS = [6, 0, 1, 2, 3]  # Sunday through Thursday

# Scraping intervals (seconds)
SCRAPING_INTERVAL_LIVE = 300  # 5 minutes during market hours
SCRAPING_INTERVAL_AFTER_HOURS = 1800  # 30 minutes after hours

# ==================== LOGGING CONFIGURATION ====================
# Mobile-friendly logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
        'verbose': {
            'format': '{asctime} {levelname} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'scrapers': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

if 'trycloudflare.com' in ALLOWED_HOSTS[0]:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Reduce cache size for mobile
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Reduced for mobile memory
        }
    }
}

# Database connection pool for better mobile performance
DATABASE_POOL_ARGS = {
    'max_overflow': 5,
    'pool_size': 3,
    'recycle': 300,
}

# ==================== API DOCUMENTATION ====================
# Swagger/OpenAPI settings (optional, can be disabled to save memory)
ENABLE_SWAGGER = os.environ.get('ENABLE_SWAGGER', 'True') == 'True'

if ENABLE_SWAGGER:
    INSTALLED_APPS.append('drf_yasg')
    SWAGGER_SETTINGS = {
        'SECURITY_DEFINITIONS': None,
        'USE_SESSION_AUTH': False,
        'JSON_EDITOR': True,
        'OPERATIONS_SORTER': 'alpha',
        'DOC_EXPANSION': 'none',
        'DEFAULT_MODEL_RENDERING': 'example',
    }

# ==================== PERFORMANCE OPTIMIZATIONS ====================
# Django debug toolbar (disable for production/mobile)
DEBUG_TOOLBAR = False

# Query optimization
DJANGO_QUERY_DEBUG = False

# ==================== APP SPECIFIC SETTINGS ====================
# NEPSE API configuration
NEPSE_API_BASE_URL = "https://www.nepalstock.com.np/api/nots"
NEPSE_UNOFFICIAL_API_BASE = "https://nepalstock.com.np"

# Data retention (days)
DATA_RETENTION_DAYS = 30  # Keep 30 days of data on mobile

# Maximum scraping attempts
MAX_SCRAPING_ATTEMPTS = 3
SCRAPING_TIMEOUT = 30  # seconds

# ==================== ANDROID SPECIFIC ====================
# Path for Android shared storage
ANDROID_SHARED_STORAGE = os.path.join(
    os.environ.get('EXTERNAL_STORAGE', '/storage/emulated/0'),
    'NEPSE-Server'
)

# Create shared directory if it doesn't exist
os.makedirs(ANDROID_SHARED_STORAGE, exist_ok=True)

# Backup directory
BACKUP_DIR = os.path.join(ANDROID_SHARED_STORAGE, 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

# ==================== HEALTH CHECK ====================
# Health check endpoints
HEALTH_CHECK_ENDPOINTS = [
    '/api/status/',
    '/health/',
    '/api/cron/test/',
]



# ==================== FALLBACK SETTINGS ====================
# If certain services are unavailable, fall back to simpler alternatives
USE_SQLITE_FALLBACK = True
USE_MEMORY_BROKER_FALLBACK = True
DISABLE_CELERY_ON_ERROR = True  # Disable Celery if Redis fails