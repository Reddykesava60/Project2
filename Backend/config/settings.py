"""
Django settings for DineFlow2 project.
Multi-tenant restaurant SaaS platform.
"""

import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# In production, SECRET_KEY must be set via environment variable
_default_secret = 'django-insecure-dev-key-change-in-production' if config('DEBUG', default=False, cast=bool) else None
SECRET_KEY = config('SECRET_KEY', default=_default_secret)
if SECRET_KEY is None:
    raise ValueError("SECRET_KEY environment variable must be set in production!")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)  # Default to False for safety

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    
    # Local apps
    'apps.core',
    'apps.restaurants',
    'apps.menu',
    'apps.orders',
    'apps.users',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Daily cleanup for stale pending cash orders (tenant-scoped, idempotent)
    'apps.orders.middleware.PendingCashOrderCleanupMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Debug toolbar (only in development)
if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# Database Configuration
if config('USE_SQLITE', default=True, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='dineflow2'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='password'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = config('DEFAULT_TIMEZONE', default='Asia/Kolkata')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Settings
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=Csv()
)
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)
CORS_ALLOW_CREDENTIALS = True

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Throttling disabled for E2E testing - re-enable in production
    # 'DEFAULT_THROTTLE_CLASSES': [
    #     'rest_framework.throttling.AnonRateThrottle',
    #     'rest_framework.throttling.UserRateThrottle',
    # ],
    # 'DEFAULT_THROTTLE_RATES': {
    #     'anon': '100/hour',
    #     'user': '1000/hour',
    # },
    # Custom exception handler for consistent error responses
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('ACCESS_TOKEN_LIFETIME', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=config('REFRESH_TOKEN_LIFETIME', default=1440, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# DRF Spectacular (API Documentation)
SPECTACULAR_SETTINGS = {
    'TITLE': 'DineFlow2 API',
    'DESCRIPTION': 'Multi-tenant restaurant SaaS platform API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/v1',
}

# QR Code Settings
QR_HMAC_SECRET = config('QR_HMAC_SECRET', default='dev-qr-secret-change-in-production')

# Frontend URL
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# Currency
DEFAULT_CURRENCY = config('DEFAULT_CURRENCY', default='INR')

# Payment Gateway Configuration (Razorpay)
RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID', default='')
RAZORPAY_KEY_SECRET = config('RAZORPAY_KEY_SECRET', default='')
RAZORPAY_WEBHOOK_SECRET = config('RAZORPAY_WEBHOOK_SECRET', default='')

# RAZORPAY_LIVE_MODE: When True (default), uses REAL Razorpay cryptographic verification.
# When False, allows simulation mode if RAZORPAY_FORCE_SUCCESS is also True.
# CRITICAL: Always set to True in production!
RAZORPAY_LIVE_MODE = config('RAZORPAY_LIVE_MODE', default=True, cast=bool)

# RAZORPAY_FORCE_SUCCESS: Testing only! When True AND RAZORPAY_LIVE_MODE=False,
# skips signature verification. NEVER enable in production!
RAZORPAY_FORCE_SUCCESS = config('RAZORPAY_FORCE_SUCCESS', default=False, cast=bool)

# SKIP_UPI_PAYMENT_FLOW: Testing only! When True, UPI orders are created directly
# like cash orders (auto-approved). Skips the initiate/verify flow.
SKIP_UPI_PAYMENT_FLOW = config('SKIP_UPI_PAYMENT_FLOW', default=False, cast=bool)

# Safety check: Warn if simulation mode is enabled
if RAZORPAY_FORCE_SUCCESS and not RAZORPAY_LIVE_MODE:
    import warnings
    warnings.warn(
        "RAZORPAY_FORCE_SUCCESS=True with RAZORPAY_LIVE_MODE=False enables payment simulation. "
        "NEVER use this in production!",
        RuntimeWarning
    )

# Validate payment config in production
if not DEBUG and RAZORPAY_KEY_ID and not RAZORPAY_KEY_SECRET:
    raise ValueError("RAZORPAY_KEY_SECRET must be set if RAZORPAY_KEY_ID is configured")

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Prints to console
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@dineflow.com')
