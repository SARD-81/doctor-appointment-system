#!/bin/sh
set -e

# اجرای مایگریشن‌ها در صورت فعال بودن فلگ محیطی
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Applying database migrations..."
    python manage.py migrate --noinput
fi

# اجرای دستور ارسالی (پیش‌فرض Gunicorn)
exec "$@"