"""Production settings with all deployment-specific values supplied by environment."""

import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from django.core.exceptions import ImproperlyConfigured

from .settings import *


def _env_bool(name, default):
	return os.environ.get(name, str(default)).lower() in {'1', 'true', 'yes', 'on'}


if not os.environ.get('DJANGO_SECRET_KEY'):
	raise ImproperlyConfigured('DJANGO_SECRET_KEY must be set for production.')
if not os.environ.get('DJANGO_ALLOWED_HOSTS'):
	raise ImproperlyConfigured('DJANGO_ALLOWED_HOSTS must include the production hostname.')
parsed_public_base_url = urlsplit(PUBLIC_BASE_URL)
if (
	parsed_public_base_url.scheme != 'https'
	or not parsed_public_base_url.netloc
	or parsed_public_base_url.path not in {'', '/'}
	or parsed_public_base_url.query
	or parsed_public_base_url.fragment
):
	raise ImproperlyConfigured('PUBLIC_BASE_URL must be the canonical HTTPS origin without a path.')
if parsed_public_base_url.hostname not in ALLOWED_HOSTS:
	raise ImproperlyConfigured('The PUBLIC_BASE_URL hostname must also appear in DJANGO_ALLOWED_HOSTS.')
if EMAIL_BACKEND.endswith('console.EmailBackend'):
	raise ImproperlyConfigured('Configure ICT_CLUB_EMAIL_USER and ICT_CLUB_EMAIL_PASSWORD for production email delivery.')

DEBUG = False
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = _env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool('DJANGO_HSTS_INCLUDE_SUBDOMAINS', False)
SECURE_HSTS_PRELOAD = _env_bool('DJANGO_HSTS_PRELOAD', False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'
MEDIA_ROOT = Path(os.environ.get('DJANGO_MEDIA_ROOT', str(BASE_DIR / 'media')))
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys([*CSRF_TRUSTED_ORIGINS, PUBLIC_BASE_URL]))
MIDDLEWARE = [
	'web.middleware.CanonicalHostMiddleware',
	*[
		middleware for middleware in MIDDLEWARE
		if middleware != 'web.middleware.CanonicalHostMiddleware'
	],
]
STORAGES = {
	**STORAGES,
	'staticfiles': {
		'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
	},
}

database_url = os.environ.get('DATABASE_URL', '')
if database_url:
	parsed_database_url = urlsplit(database_url)
	database_name = unquote(parsed_database_url.path.lstrip('/'))
	if parsed_database_url.scheme in {'postgres', 'postgresql', 'postgresql+psycopg'}:
		database_options = parse_qs(parsed_database_url.query)
		DATABASES = {
			'default': {
				'ENGINE': 'django.db.backends.postgresql',
				'NAME': database_name,
				'USER': unquote(parsed_database_url.username or ''),
				'PASSWORD': unquote(parsed_database_url.password or ''),
				'HOST': parsed_database_url.hostname or '',
				'PORT': parsed_database_url.port or '',
				'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
				'OPTIONS': {
					key: values[-1]
					for key, values in database_options.items()
					if key == 'sslmode'
				},
			},
		}
	elif parsed_database_url.scheme == 'sqlite':
		DATABASES = {
			'default': {
				'ENGINE': 'django.db.backends.sqlite3',
				'NAME': (
					'/' + parsed_database_url.path.lstrip('/')
					if parsed_database_url.path.startswith('//')
					else database_name or str(BASE_DIR / 'db.sqlite3')
				),
			},
		}
	else:
		raise ImproperlyConfigured('DATABASE_URL must use sqlite or PostgreSQL.')

LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'handlers': {'console': {'class': 'logging.StreamHandler'}},
	'loggers': {
		'django': {'handlers': ['console'], 'level': 'WARNING'},
		'django.security': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
	},
}
