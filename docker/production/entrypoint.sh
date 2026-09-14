#!/bin/sh
set -e

case "${RUN_MIGRATIONS:-false}" in
  true|TRUE|1|yes|YES)
    echo "Applying database migrations..."
    python manage.py migrate --noinput
    ;;
esac

exec "$@"
