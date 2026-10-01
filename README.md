# Blessed Sacrament Secondary School ICT Club

Existing Django website for the BSK ICT Club at Blessed Sacrament Secondary School Kimaanya, Masaka City, Uganda.

## Local development

Requirements: Python 3.10 or newer. Windows PowerShell examples:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DJANGO_SECRET_KEY = "a-local-development-only-secret"
python manage.py migrate
python manage.py runserver
```

The default development configuration uses SQLite, debug mode, and the console email backend when SMTP credentials are absent. Configure `ICT_CLUB_EMAIL_*` to send contact-form emails. Website submissions are also stored in the leadership contact inbox.

Do not use `runserver` as a production server. Never commit `.env` files, database backups, or production media.

## Production deployment

The project supports a Django-compatible Linux/Python host. No host, public domain, or paid service is selected or configured here. Hosting plans, persistence, and custom-domain pricing vary by provider; verify current provider documentation before deployment.

### 1. Choose the runtime and storage

Use Python 3.10+ and install dependencies from `requirements.txt`. The included `Procfile` starts Gunicorn; configure the same command as the platform start command if it does not read Procfiles:

```text
gunicorn ICT_CLUB.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 60
```

Use a persistent database for production. SQLite is supported for a small, single-instance deployment only when the database file is on persistent storage. PostgreSQL is supported through `DATABASE_URL` and is the preferred option for concurrent writes or multiple application instances. Installations using the PostgreSQL backend include `psycopg` in the requirements.

Uploaded project images use Django's file storage. Mount persistent storage and set `DJANGO_MEDIA_ROOT` to it, or configure a separately managed object-storage backend before using ephemeral/multi-instance hosting. Static files are collected into `staticfiles/` and served with WhiteNoise; user uploads are not served by Django in production.

### 2. Configure environment variables

Set these in the hosting dashboard or secret manager; `.env.example` documents the names and contains placeholders only:

* `DJANGO_SETTINGS_MODULE=ICT_CLUB.production_settings`
* `DJANGO_SECRET_KEY`: a newly generated, private, long random value. Do not reuse the development key.
* `DJANGO_ALLOWED_HOSTS`: comma-separated exact hostnames for this deployment.
* `PUBLIC_BASE_URL`: the canonical HTTPS origin, with no path, such as `https://<your-domain>`. Its hostname must be in `DJANGO_ALLOWED_HOSTS`.
* `DJANGO_CSRF_TRUSTED_ORIGINS`: comma-separated HTTPS origins for the site and any real trusted admin origin.
* `ICT_CLUB_EMAIL_USER` and `ICT_CLUB_EMAIL_PASSWORD`, plus the `ICT_CLUB_EMAIL_HOST`, `ICT_CLUB_EMAIL_PORT`, and `ICT_CLUB_EMAIL_USE_TLS` required by the selected email provider. Production startup intentionally refuses the console email backend.
* `DATABASE_URL` for PostgreSQL, or omit it to use SQLite. Put credentials in the provider's secret manager and follow that provider's TLS/SSL requirements.
* `DJANGO_MEDIA_ROOT` if the host requires a mounted persistent media directory.

Generate a key locally without sharing it (for example, `python -c "import secrets; print(secrets.token_urlsafe(64))"`), then put it directly into the hosting provider's secret manager. Do not paste the generated value into source control or this guide.

Keep `DJANGO_SECURE_SSL_REDIRECT=true` when TLS terminates at a trusted proxy that sets `X-Forwarded-Proto`. The included production settings enable secure session/CSRF cookies and HSTS. Keep HSTS subdomains/preload disabled unless every subdomain is HTTPS-ready. If the platform uses a different trusted-proxy header, adjust `SECURE_PROXY_SSL_HEADER` only to match its documented behavior.

Set `ICT_CLUB_INITIAL_PASSWORD_<USERNAME>` variables only when provisioning a missing leader account. Existing leader passwords are not reset at login or deployment. Initial values are read only when a user record is first created; maintain and rotate accounts through the normal secure account-management process.

### 3. Build and deploy

Run these commands in the release/build environment, not against a local or production database by accident:

```text
python manage.py check --deploy --settings=ICT_CLUB.production_settings
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

The deployment needs outbound access to the configured SMTP provider. Configure `/health/` as the platform health-check path; it verifies a database connection and returns a minimal response. The platform must terminate HTTPS and route requests to the Gunicorn process.

### 4. DNS, HTTPS, media and recovery

Add the custom domain at the hosting provider, then publish only the DNS records its current documentation specifies. Enable and verify HTTPS before directing public traffic to the site. Set `PUBLIC_BASE_URL`, allowed hosts, and CSRF origins to that actual domain; no domain is presumed by this project.

Confirm that uploaded images survive a redeploy and are available to every running instance. Configure automated database backups and test a restore before launch. For PostgreSQL, use the provider's supported backup/export mechanism (or `pg_dump` where appropriate); for SQLite, stop writes or use SQLite's online backup mechanism before copying the database file. Back up persistent media separately.

## Search discovery

Public pages have page-specific titles/descriptions, canonical links, Open Graph metadata, and Organization/WebSite JSON-LD. `/sitemap.xml` lists only the public home, about, projects, team, and contact pages. `/robots.txt` points crawlers to that sitemap and discourages crawling private records/admin/health paths; robots rules are not access control.

After the real HTTPS domain is live:

1. Verify that domain or URL-prefix property in Google Search Console using a verification method Google currently supports.
2. Open **Sitemaps**, submit `https://<your-domain>/sitemap.xml`, and review processing errors.
3. Inspect the home, About, Projects, Team, and Contact URLs. Check the selected canonical and request indexing for eligible pages as needed.
4. Review indexing/canonical issues and, after data accumulates, search queries, impressions, clicks, and click-through rates. Update useful page copy based on actual club information; rankings and timing cannot be guaranteed.
5. Analytics is optional. If added, configure a privacy notice/consent approach appropriate to the visitors and applicable law; no analytics service is installed by default.

## Performance and maintenance checks

Run before a release:

```text
python manage.py check
python manage.py check --deploy --settings=ICT_CLUB.production_settings
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
```

The checked-in original images are retained; optimized WebP copies and smaller responsive variants are used for supported public imagery. WhiteNoise emits compressed, fingerprinted static assets. Hosting/CDN gzip or Brotli, HTTP/2/3, caching behavior beyond these static files, and persistent media storage depend on the selected provider and are not assumed to be active here.

Measure actual pages using Lighthouse in mobile and desktop modes, PageSpeed Insights after deployment, and browser developer tools at mobile, tablet, laptop, and desktop widths. Aim for field Core Web Vitals of LCP ≤2.5 s, INP ≤200 ms, and CLS ≤0.1, but assess real-user measurements; no scores or ranking gains are claimed without those measurements.
