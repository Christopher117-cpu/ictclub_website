from pathlib import Path
import os
import secrets
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# DEBUG
# ============================================================

# Render production = False
# Local development = True unless DJANGO_DEBUG is explicitly set.

DEBUG = os.environ.get(
    "DJANGO_DEBUG",
    "false",
).lower() in ("true", "1", "yes", "on")


# ============================================================
# SECRET KEY
# ============================================================

# Use Render environment variable if available.
# Otherwise generate a key automatically so deployment does
# not fail because a secret was not manually configured.

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY"
)

if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(64)


# ============================================================
# ALLOWED HOSTS
# ============================================================

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "testserver",
    "ictclub-website.onrender.com",
]


# Automatically accept Render's hostname.
RENDER_EXTERNAL_HOSTNAME = os.environ.get(
    "RENDER_EXTERNAL_HOSTNAME"
)

if RENDER_EXTERNAL_HOSTNAME:
    if RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(
            RENDER_EXTERNAL_HOSTNAME
        )


# ============================================================
# CSRF
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    "https://ictclub-website.onrender.com",
]


# ============================================================
# PUBLIC WEBSITE URL
# ============================================================

PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL",
    "https://ictclub-website.onrender.com",
).rstrip("/")


# ============================================================
# ICT CLUB INITIAL PASSWORDS
# ============================================================

# These are optional.
#
# If the environment variables already exist, Django will use
# them.
#
# If they do not exist, the application can still start.

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

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    parsed_database_url = urlparse(DATABASE_URL)
    database_name = parsed_database_url.path.lstrip("/")

    if parsed_database_url.scheme in {
        "postgres",
        "postgresql",
        "postgresql+psycopg",
        "postgresql+psycopg2",
    }:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": database_name,
                "USER": parsed_database_url.username or "",
                "PASSWORD": parsed_database_url.password or "",
                "HOST": parsed_database_url.hostname or "",
                "PORT": parsed_database_url.port or "",
                "CONN_MAX_AGE": 60,
            }
        }
    elif parsed_database_url.scheme == "sqlite":
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
    else:
        raise ImproperlyConfigured(
            "DATABASE_URL must use postgres or sqlite."
        )
else:
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


# Keep this simple and compatible with your current project.
STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage.FileSystemStorage"
        ),
    },

    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedStaticFilesStorage"
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
except (TypeError, ValueError):
    EMAIL_PORT = 587


EMAIL_HOST_USER = os.environ.get(
    "ICT_CLUB_EMAIL_USER",
    "",
)

EMAIL_HOST_PASSWORD = os.environ.get(
    "ICT_CLUB_EMAIL_PASSWORD",
    "",
)


EMAIL_USE_TLS = (
    os.environ.get(
        "ICT_CLUB_EMAIL_USE_TLS",
        "true",
    ).lower()
    in ("true", "1", "yes", "on")
)


# SMTP when configured.
# Console backend otherwise.
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
# RENDER HTTPS
# ============================================================

# Render sits behind a proxy.
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# Redirect to HTTPS in production while keeping local development easy.
SECURE_SSL_REDIRECT = not DEBUG


# ============================================================
# COOKIES
# ============================================================

SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SECURE = not DEBUG

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SAMESITE = "Lax"


# ============================================================
# SECURITY HEADERS
# ============================================================

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"

SECURE_REFERRER_POLICY = "same-origin"


# ============================================================
# HSTS
# ============================================================

# Disabled initially to avoid deployment problems.

SECURE_HSTS_SECONDS = 0

SECURE_HSTS_INCLUDE_SUBDOMAINS = False

SECURE_HSTS_PRELOAD = False


# ============================================================
# UPLOAD LIMITS
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
