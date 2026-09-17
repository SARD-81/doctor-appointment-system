# Doctor Appointment System

A server-rendered, RTL doctor appointment platform built with Django 5.2, PostgreSQL,
Redis, Gunicorn, Nginx, and Docker.

The current implementation covers the mandatory bootcamp scope:

- email/password registration with email OTP verification;
- case-insensitive email login and database-level email uniqueness;
- active-doctor discovery by name or specialty;
- doctor details and future available appointment slots;
- atomic booking with row locks, fee snapshots, wallet debit, and an auditable ledger;
- simulated wallet top-up (no external payment gateway);
- booking confirmation email after a successful database commit;
- patient appointment history;
- admin-controlled completion of visits with actor/time audit fields;
- one review and rating per completed appointment;
- responsive RTL UI with persistent light/dark themes;
- development and production Docker Compose topologies.

Google OAuth is optional bonus scope from the brief and is **not implemented**.

## Architecture

The project follows Django MVT with explicit service-layer boundaries for OTP, wallet,
booking, and review business rules. PostgreSQL constraints protect critical invariants,
including one booking per slot, non-negative balances, transaction/reference consistency,
one payment ledger row per appointment, and ratings from 1 through 5.

Architecture sources of truth:

- [Architecture index](documents/architecture/README.md)
- [ERD](documents/architecture/erd.md)
- [Booking sequence](documents/architecture/uml-booking-sequence.md)
- [ADR index](documents/adr/README.md)
- [Implementation status](documents/architecture/implementation-status.md)

## Prerequisites

- Docker Engine with Docker Compose v2 (recommended), or
- Python 3.12 and PostgreSQL 16 for a host-based setup.

## Development with Docker

From a fresh clone:

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Open <http://localhost:8000>.

Create repeatable local demonstration data:

```bash
docker compose exec web python manage.py seed_demo_data
```

The seed command is idempotent for the current development day and refuses to run unless
`ALLOW_DEMO_DATA=True`; production settings force that flag off.

Useful commands:

```bash
docker compose ps
docker compose logs -f web
docker compose exec web pytest -q
docker compose down
```

`docker compose down -v` permanently removes the local PostgreSQL volume. Use it only
when that data loss is intentional.

## Host-based development

Create and activate a virtual environment, then install development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

PowerShell activation on Windows 11:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Ensure the PostgreSQL values in `.env` point to a running database, then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The default local email backend prints OTP and booking emails to the terminal. Redis is
not required for the single-process development server; Compose overrides the cache URL
and uses Redis so its behavior matches a multi-process deployment.

## Quality gates

Run all required checks before opening a pull request:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
ruff check .
ruff format --check .
coverage run -m pytest -q
coverage report --fail-under=95
pip-audit -r requirements-dev.txt --progress-spinner off
```

CI runs these checks against PostgreSQL and also validates production settings and both
Compose files.

## Vercel preview / demo deployment

Vercel is supported as a **non-production preview environment** only. The real production
contract remains the Docker + Gunicorn + Nginx topology documented below.

The preview environment uses `config.settings.preview`, which keeps `DEBUG=False`, secure
cookies and HTTPS redirects, but intentionally avoids the production-only Redis and SMTP
requirements. OTP/rate-limit cache state is stored in a shared PostgreSQL database cache
so it remains available across serverless function instances.

For a Neon-backed preview, configure these Vercel environment variables as secrets:

```text
SECRET_KEY=<unique-random-secret>
DATABASE_URL=<pooled-neon-connection-string>
DATABASE_URL_UNPOOLED=<direct-neon-connection-string>
TIME_ZONE=Asia/Tehran
```

`DATABASE_URL` is used by normal application traffic. `DATABASE_URL_UNPOOLED` is used only
by the Vercel build bootstrap for schema migrations. Never commit either connection string
or the real `SECRET_KEY`.

Optional email variables can be added when end-to-end OTP delivery is required:

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=<smtp-host>
EMAIL_PORT=587
EMAIL_HOST_USER=<smtp-user>
EMAIL_HOST_PASSWORD=<smtp-password>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=<sender-address>
```

Without SMTP variables, preview deployments keep Django's console email backend. Public
pages remain usable, but a remote visitor cannot receive OTP email directly.

Vercel automatically exposes the `VERCEL` environment flag. The project uses it to select
preview settings for WSGI and management commands. During each Vercel build,
`scripts/vercel_build.py` runs the following against the isolated preview database:

1. Django migrations using `DATABASE_URL_UNPOOLED` when available;
2. creation of the shared database cache table;
3. idempotent demo doctor/specialty/slot seeding;
4. `collectstatic`.

Local and Docker environments continue to use the existing `POSTGRES_*` variables whenever
`DATABASE_URL` is empty.

## Production deployment

The production Compose topology contains:

- PostgreSQL 16 on an internal network with persistent storage;
- Redis for shared OTP/rate-limit state across Gunicorn workers;
- a non-root Gunicorn application container;
- Nginx for reverse proxying and static/media delivery.

Create the production environment and replace **every** placeholder:

```bash
cp .env.production.example .env.production
```

Required production configuration includes a random 50+ character `SECRET_KEY`, the
public `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, PostgreSQL credentials, SMTP
credentials, and secure-cookie/HSTS settings. The sample configuration assumes an
external TLS-terminating proxy sends `X-Forwarded-Proto: https` to Nginx. Do not expose
the HTTP listener directly to the public internet.

HSTS starts disabled in the sample. Enable it only after HTTPS is verified for the
production domain; enable subdomain coverage and browser preload only when every affected
subdomain is permanently HTTPS-capable.

Validate, initialize, and start:

```bash
docker compose -f compose.production.yml config --quiet
docker compose -f compose.production.yml build
docker compose -f compose.production.yml run --rm web python manage.py migrate --noinput
docker compose -f compose.production.yml run --rm web python manage.py collectstatic --noinput
docker compose -f compose.production.yml up -d
docker compose -f compose.production.yml ps
curl http://127.0.0.1:8080/healthz/
```

Nginx binds to `127.0.0.1:8080` by default for a local TLS proxy. Override
`PROXY_BIND_ADDRESS` or `PROXY_HTTP_PORT` only as part of a reviewed deployment
topology.

Before release, run the deployment check with the real production environment:

```bash
docker compose -f compose.production.yml run --rm web python manage.py check --deploy
```

## Repository workflow

The repository's current release baseline is `main`. Work is performed on short-lived
issue branches and merged through reviewed, green pull requests. See
[the Git workflow](documents/git-workflow.md) and
[Definition of Done](documents/definition-of-done.md).

## Project layout

```text
apps/                   Django domain applications
config/                 URL, WSGI/ASGI, and environment settings
documents/              Architecture, ADRs, workflow, and team contracts
docker/                 Development/production images and Nginx configuration
static/                  Tokenized RTL styles and JavaScript
templates/               Django templates and shared UI components
compose.yml              Development services
compose.production.yml   Production services
```
