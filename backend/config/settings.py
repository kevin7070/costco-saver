"""Django settings for costco-saver."""

import os
from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

# =============================================================================
# Core Django
# =============================================================================

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
# Fail-secure: default DEBUG off so a prod box that forgets to set it stays safe.
# Dev/test set DEBUG=True explicitly (backend/.env, CI env).
DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Never run production on the insecure dev key.
if not DEBUG and SECRET_KEY == "dev-insecure-change-me":
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is False.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "axes",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_celery_beat",
    # Local apps
    "apps.users",
    "apps.items",
    "apps.parsers",
    "apps.receipts",
    "apps.pricing",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# =============================================================================
# Database
# =============================================================================

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///db.sqlite3")

if DATABASE_URL.startswith("postgres"):
    # Parse postgres://user:pass@host:port/dbname
    import urllib.parse

    url = urllib.parse.urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": url.path[1:],
            "USER": url.username,
            "PASSWORD": url.password,
            "HOST": url.hostname,
            "PORT": url.port or 5432,
        }
    }
else:
    # sqlite fallback (dev only)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# =============================================================================
# Auth
# =============================================================================

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesBackend",  # Must be first for rate limiting
    "django.contrib.auth.backends.ModelBackend",
]

# django-axes — brute-force protection on login
AXES_FAILURE_LIMIT = 10
AXES_COOLOFF_TIME = 1  # hours
AXES_RESET_ON_SUCCESS = True
# Lock by username AND by IP as independent groups: protects one account from
# distributed credential stuffing (username lock) and throttles one source
# (IP lock). Locking a username is a DoS-on-victim vector, mitigated by
# password-reset auto-unlock + the 1h cooloff.
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]

# =============================================================================
# i18n / Time
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =============================================================================
# Static
# =============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"  # uploaded receipt images
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Upload cap — receipts are images/PDFs; reject larger bodies early.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# =============================================================================
# Django REST Framework
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.users.authentication.CookieJWTAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "auth_login": "10/minute",
        "register": "5/hour",
        "password_reset": "3/hour",
        "password_change": "2/hour",
        "profile_update": "2/hour",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# =============================================================================
# SimpleJWT
# =============================================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Rotate the refresh token on every use and blacklist the old one, so a
    # leaked refresh token is usable at most once. Minor multi-tab race is
    # acceptable (frontend redirects to /login on a refresh 401).
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.environ.get("JWT_SIGNING_KEY", SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUDIENCE": os.environ.get("JWT_AUDIENCE", "costco-saver-api"),
    "ISSUER": os.environ.get("JWT_ISSUER", "costco-saver"),
}

# JWT cookie settings
JWT_COOKIE_SECURE = not DEBUG
JWT_COOKIE_SAMESITE = "Lax"
JWT_COOKIE_PATH = "/"

# =============================================================================
# Production security headers (active when DEBUG is off)
# =============================================================================

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    # Behind the Apache reverse proxy that terminates TLS.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    # Comma-separated prod origins, e.g. https://costco.example.com
    CSRF_TRUSTED_ORIGINS = [
        o for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o
    ]

# =============================================================================
# Email
# =============================================================================

# Base URL of the frontend, used to build links in transactional emails.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:9100")

if os.environ.get("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["EMAIL_HOST"]
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================================================================
# Celery (background tasks / scheduling)
# =============================================================================

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CELERY_TASK_DEFAULT_QUEUE = "default"
# Receipt parsing runs on a dedicated single-concurrency queue so the vision
# LLM endpoint (one job at a time) is never hit concurrently.
CELERY_TASK_ROUTES = {
    "apps.receipts.tasks.parse_receipt": {"queue": "receipt_parse"},
    "apps.pricing.tasks.refresh_prices": {"queue": "price_refresh"},
}
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
# Scheduled jobs — DatabaseScheduler syncs these into django_celery_beat on boot.
CELERY_BEAT_SCHEDULE = {
    "refresh-due-prices": {
        # Daily fan-out: queue a refresh for every product whose price is stale.
        "task": "apps.pricing.tasks.enqueue_due_checks",
        "schedule": crontab(hour=6, minute=0),
    },
    "purge-expired-receipts": {
        # Retention: drop receipts (rows + files) past RECEIPT_RETENTION_DAYS.
        "task": "apps.receipts.tasks.purge_expired_receipts",
        "schedule": crontab(hour=3, minute=0),
    },
}

# How long a receipt (row + uploaded file) is kept before the daily purge.
RECEIPT_RETENTION_DAYS = int(os.environ.get("RECEIPT_RETENTION_DAYS", "365"))

# =============================================================================
# Receipt parsing — self-hosted vision LLM endpoint
# =============================================================================

# Provided by Kevin's GPU box; app only calls the endpoint (no local model).
RECEIPT_LLM_BASE_URL = os.environ.get("RECEIPT_LLM_BASE_URL", "")
RECEIPT_LLM_MODEL = os.environ.get("RECEIPT_LLM_MODEL", "")
# Secret — bearer token, kept in env only, never committed.
RECEIPT_LLM_API_KEY = os.environ.get("RECEIPT_LLM_API_KEY", "")
RECEIPT_LLM_TIMEOUT = int(os.environ.get("RECEIPT_LLM_TIMEOUT", "300"))

# =============================================================================
# Price provider — pluggable, resolved at runtime (default: no-op NullProvider)
# =============================================================================

# Dotted path to the PriceProvider implementation. The default ships in-repo and
# does nothing; a real provider is supplied by the deployment environment only.
PRICE_PROVIDER = os.environ.get("PRICE_PROVIDER", "apps.pricing.null_provider.NullProvider")
PRICE_PROVIDER_URL = os.environ.get("PRICE_PROVIDER_URL", "")
PRICE_PROVIDER_API_KEY = os.environ.get("PRICE_PROVIDER_API_KEY", "")
PRICE_PROVIDER_TIMEOUT = int(os.environ.get("PRICE_PROVIDER_TIMEOUT", "60"))
PRICE_CHECK_ADJUSTMENT_DAYS = int(os.environ.get("PRICE_CHECK_ADJUSTMENT_DAYS", "30"))
