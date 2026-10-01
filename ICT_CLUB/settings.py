```python
"""
Django settings for ICT_CLUB project.

Production-ready configuration for:
- Local development
- Render deployment
- WhiteNoise static files
- Environment-based secrets
- HTTPS/security settings
- SQLite database
- ICT Club leader initial passwords
"""

from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# ENVIRONMENT HELPERS
# ============================================================

def env_bool(name, default=False):
    """
    Read a boolean environment variable safely.

    Examples:
        true, 1, yes, on  -> True
        false, 0, no, off -> False
    """
    value = os.environ.get(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "true",
        "1",
        "yes",
        "on",
    }


def env_list(name, default=None):
    """
    Read a comma-separated environment variable.
    """
    value = os.environ.get(name)

    if value is None:
        return default or []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# ============================================================
# SECURITY
# ============================================================

# IMPORTANT:
# Set DJANGO_SECRET_KEY in Render Environment Variables.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    if env_bool("DJANGO_DEBUG", default=False):
        # Development-only fallback.
        SECRET_KEY = (
            "django-insecure-local-development-only-do-not-use-in-production"
        )
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set when DEBUG=False."
        )


# ============================================================
# DEBUG
# ============================================================

# Production default is FALSE.
DEBUG = env_bool("DJANGO_DEBUG", default=False)


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "testserver",
]


# Render automatically provides this environment variable.
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# Your current Render hostname.
if "ictclub-website.onrender.com" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("ictclub-website.onrender.com")


# Additional hosts can be supplied through Render if needed.
ALLOWED_HOSTS.extend(
    host
    for host in env_list("DJANGO_ALLOWED_HOSTS")
    if host not in ALLOWED_HOSTS
)


# ============================================================
# CSRF TRUSTED ORIGINS
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    "https://ictclub-website.onrender.com",
]

# Allow additional origins through environment variables.
for origin in env_list("DJANGO_CSRF_TRUSTED_ORIGINS"):
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)


# ============================================================
# PUBLIC WEBSITE URL
# ============================================================

PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL",
    "https://ictclub-website.onrender.com",
).rstrip("/")


# ============================================================
# ICT CLUB INITIAL LEADER PASSWORDS
# ============================================================

LEADER_USERNAMES = (
    "codestar",
    "patron",
    "secretary",
    "speaker",
    "treasurer",
    "projectsmanager",
    "mobiliser",
)

LEADER_INITIAL_PASSWORDS = {
    username: os.environ.get(
        f"ICT_CLUB_INITIAL_PASSWORD_{username.upper()}",
        "",
    )
    for username in LEADER_USERNAMES
}


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",

    "web",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise serves static files directly from Django.
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "ICT_CLUB.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                "web.context_processors.public_announcements",
                "web.context_processors.seo_metadata",
            ],
        },
    },
]


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "ICT_CLUB.wsgi.application"


# ============================================================
# DATABASE
# ============================================================

# IMPORTANT:
# This keeps your current SQLite database setup.
#
# SQLite is fine for getting the website running.
# For a serious multi-user production system, especially one
# storing important school records, PostgreSQL is recommended
# later.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Kampala"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"


# WhiteNoise storage with compression and hashed filenames.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },

    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
        ),
    },
}


# ============================================================
# MEDIA FILES
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# EMAIL
# ============================================================

EMAIL_HOST = os.environ.get(
    "ICT_CLUB_EMAIL_HOST",
    "smtp.gmail.com",
)

EMAIL_PORT = int(
    os.environ.get(
        "ICT_CLUB_EMAIL_PORT",
        "587",
    )
)

EMAIL_HOST_USER = os.environ.get(
    "ICT_CLUB_EMAIL_USER",
    "",
)

EMAIL_HOST_PASSWORD = os.environ.get(
    "ICT_CLUB_EMAIL_PASSWORD",
    "",
)

EMAIL_USE_TLS = env_bool(
    "ICT_CLUB_EMAIL_USE_TLS",
    default=True,
)


# Use SMTP when credentials exist.
# Otherwise use console backend during development.
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = (
        "django.core.mail.backends.smtp.EmailBackend"
    )
else:
    EMAIL_BACKEND = (
        "django.core.mail.backends.console.EmailBackend"
    )


DEFAULT_FROM_EMAIL = os.environ.get(
    "ICT_CLUB_DEFAULT_FROM_EMAIL",
    "ictclubbsk@gmail.com",
)


# ============================================================
# HTTPS / PROXY SECURITY
# ============================================================

# Render terminates HTTPS at its proxy and forwards the request
# to Django. This tells Django to trust Render's HTTPS header.
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# Redirect HTTP requests to HTTPS in production.
SECURE_SSL_REDIRECT = env_bool(
    "DJANGO_SECURE_SSL_REDIRECT",
    default=True,
)


# ============================================================
# SECURE COOKIES
# ============================================================

SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SECURE = not DEBUG


# Prevent JavaScript from accessing the session cookie.
SESSION_COOKIE_HTTPONLY = True


# ============================================================
# COOKIE SETTINGS
# ============================================================

SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SAMESITE = "Lax"


# ============================================================
# SECURITY HEADERS
# ============================================================

SECURE_BROWSER_XSS_FILTER = True

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"


# ============================================================
# HSTS
# ============================================================

# HSTS tells browsers to use HTTPS for this site.
#
# Start conservatively. Once HTTPS is confirmed to work
# correctly, this can safely be increased.

SECURE_HSTS_SECONDS = int(
    os.environ.get(
        "DJANGO_SECURE_HSTS_SECONDS",
        "31536000" if not DEBUG else "0",
    )
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG

SECURE_HSTS_PRELOAD = not DEBUG


# ============================================================
# CONTENT SECURITY / REFERRER
# ============================================================

SECURE_REFERRER_POLICY = "same-origin"


# ============================================================
# FILE UPLOAD LIMIT
# ============================================================

# Maximum request body size: 10 MB.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Maximum number of uploaded fields.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# PRODUCTION VALIDATION
# ============================================================

if not DEBUG:

    # Production must have a real secret key.
    if not os.environ.get("DJANGO_SECRET_KEY"):
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY is required in production."
        )

    # Production should not accidentally use localhost only.
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "ALLOWED_HOSTS must contain at least one host."
        )
```
