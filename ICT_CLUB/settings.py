```python
"""
Django settings for ICT_CLUB project.

Configured for:
- Local development
- Render deployment
- Django 5.2
- WhiteNoise
- SQLite
- Environment variables
- ICT Club leader accounts
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

def get_bool(name, default=False):
    value = os.environ.get(name)

    if value is None:
        return default

    return value.strip().lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def get_list(name, default=None):
    value = os.environ.get(name)

    if not value:
        return default or []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# ============================================================
# SECRET KEY
# ============================================================

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    if get_bool("DJANGO_DEBUG", True):
        # Only used during local development.
        SECRET_KEY = (
            "django-insecure-local-development-only"
        )
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be configured in production."
        )


# ============================================================
# DEBUG
# ============================================================

# IMPORTANT:
# Render should have:
#
# DJANGO_DEBUG=false
#
# Local development defaults to True if the variable is absent.

DEBUG = get_bool("DJANGO_DEBUG", True)


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "testserver",
    "ictclub-website.onrender.com",
]


# Render automatically provides the deployed hostname.
RENDER_EXTERNAL_HOSTNAME = os.environ.get(
    "RENDER_EXTERNAL_HOSTNAME"
)

if RENDER_EXTERNAL_HOSTNAME:
    if RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# Additional hosts can be supplied through Render.
for host in get_list("DJANGO_ALLOWED_HOSTS"):
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)


# ============================================================
# CSRF TRUSTED ORIGINS
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    "https://ictclub-website.onrender.com",
]

for origin in get_list("DJANGO_CSRF_TRUSTED_ORIGINS"):
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)


# ============================================================
# PUBLIC BASE URL
# ============================================================

PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL",
    "https://ictclub-website.onrender.com",
).rstrip("/")


# ============================================================
# ICT CLUB INITIAL LEADER PASSWORDS
# ============================================================

LEADER_INITIAL_PASSWORDS = {
    "codestar": os.environ.get(
        "ICT_CLUB_INITIAL_PASSWORD_CODESTAR",
        "",
    ),

    "patron": os.environ.get(
        "ICT_CLUB_INITIAL_PASSWORD_PATRON",
        "",
    ),

    "secretary": os.environ.get(
        "ICT_CLUB_INITIAL_PASSWORD_SECRETARY",
        "",
    ),

    "speaker": os.environ.get(
        "ICT_CLUB_INITIAL_PASSWORD_SPEAKER",
        "",
    ),

    "treasurer": os.environ.get(
        "ICT_CLUB_INITIAL_PASSWORD_TREASURER",
        "",
    ),

    "projectsmanager": os.environ.get(
        "ICT_CLUB_INITIAL_PASSWORD_PROJECTSMANAGER",
        "",
    ),

    "mobiliser": os.environ.get(
        "ICT_CLUB_INITIAL_PASSWORD_MOBILISER",
        "",
    ),
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

    # WhiteNoise for static files.
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
        "BACKEND": (
            "django.template.backends.django.DjangoTemplates"
        ),

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

# Keep SQLite for now so the existing project continues
# working without requiring a database migration.

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


# Keep the standard storage backend because it is
# compatible with your existing project.

STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage.FileSystemStorage"
        ),
    },

    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedStaticFilesStorage"
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

try:
    EMAIL_PORT = int(
        os.environ.get(
            "ICT_CLUB_EMAIL_PORT",
            "587",
        )
    )
except ValueError:
    EMAIL_PORT = 587


EMAIL_HOST_USER = os.environ.get(
    "ICT_CLUB_EMAIL_USER",
    "",
)

EMAIL_HOST_PASSWORD = os.environ.get(
    "ICT_CLUB_EMAIL_PASSWORD",
    "",
)

EMAIL_USE_TLS = get_bool(
    "ICT_CLUB_EMAIL_USE_TLS",
    True,
)


# Use SMTP only when credentials have been configured.
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:

    EMAIL_BACKEND = (
        "django.core.mail.backends.smtp.EmailBackend"
    )

else:

    # Safe fallback for development.
    EMAIL_BACKEND = (
        "django.core.mail.backends.console.EmailBackend"
    )


DEFAULT_FROM_EMAIL = os.environ.get(
    "ICT_CLUB_DEFAULT_FROM_EMAIL",
    "ictclubbsk@gmail.com",
)


# ============================================================
# RENDER / HTTPS
# ============================================================

# Render uses a reverse proxy.
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# Do NOT force HTTPS by default yet.
#
# Once the website is confirmed working correctly on Render,
# you can set:
#
# DJANGO_SECURE_SSL_REDIRECT=true
#
SECURE_SSL_REDIRECT = get_bool(
    "DJANGO_SECURE_SSL_REDIRECT",
    False,
)


# ============================================================
# SECURE COOKIES
# ============================================================

SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SECURE = not DEBUG

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SAMESITE = "Lax"


# ============================================================
# BASIC SECURITY HEADERS
# ============================================================

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"

SECURE_REFERRER_POLICY = "same-origin"


# ============================================================
# HSTS
# ============================================================

# Disabled by default to avoid locking the site into HTTPS
# before deployment has been fully verified.

SECURE_HSTS_SECONDS = int(
    os.environ.get(
        "DJANGO_SECURE_HSTS_SECONDS",
        "0",
    )
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    SECURE_HSTS_SECONDS > 0
)

SECURE_HSTS_PRELOAD = (
    SECURE_HSTS_SECONDS > 0
)


# ============================================================
# FILE UPLOAD LIMITS
# ============================================================

DATA_UPLOAD_MAX_MEMORY_SIZE = (
    10 * 1024 * 1024
)

DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)
```
