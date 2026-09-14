# Doctor Appointment System

Production-ready doctor appointment booking system built with Django, PostgreSQL and Docker, featuring OTP authentication, wallet payments, reviews, scheduling, and Google OAuth.

## Docker development

Create the local environment file and start the development services:

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

The application is available at `http://localhost:8000`.

Useful commands:

```bash
docker compose logs -f web
docker compose ps
docker compose down
```

Use `docker compose down -v` only when you intentionally want to delete the local PostgreSQL volume and its data.

## Docker production

Create a production environment file from the committed template and replace all placeholder values before deployment:

```bash
cp .env.production.example .env.production
```

Build the production image and prepare database/static assets:

```bash
docker compose -f compose.production.yml build
docker compose -f compose.production.yml run --rm web python manage.py migrate --noinput
docker compose -f compose.production.yml run --rm web python manage.py collectstatic --noinput
docker compose -f compose.production.yml up -d
docker compose -f compose.production.yml ps
docker compose -f compose.production.yml logs -f nginx
```

The production stack exposes Nginx on port 80. PostgreSQL is kept on the internal Compose network and is persisted in the `postgres_data_prod` volume. Production deployment requires real secret values, an appropriate `ALLOWED_HOSTS`, and HTTPS-aware secure-cookie/HSTS settings.

## Verification

Before opening or merging a Docker PR, run the standard Django checks and the relevant Compose validation:

```bash
python manage.py check
python manage.py check --deploy
docker compose -f compose.production.yml config
```

Docker runtime validation must be reported separately from the standard CI quality job if Docker is unavailable in the local environment.
