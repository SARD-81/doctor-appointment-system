FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY . /app/

RUN mkdir -p /app/staticfiles && \
    chown -R appuser:appgroup /app

COPY docker/production/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# تزریق متغیرهای موقت صرفاً جهت عبور امن از مرحله جمع‌آوری استاتیک
RUN DJANGO_SETTINGS_MODULE=config.settings.production \
    SECRET_KEY="build-time-insecure-key-for-collectstatic-only" \
    POSTGRES_DB="dummy_db" \
    POSTGRES_USER="dummy_user" \
    POSTGRES_PASSWORD="dummy_password" \
    POSTGRES_HOST="127.0.0.1" \
    POSTGRES_PORT="5432" \
    python manage.py collectstatic --noinput

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]