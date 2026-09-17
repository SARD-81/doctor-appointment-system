"""Prepare the isolated Vercel preview environment during deployment."""

import os

# Migrations must use Neon's direct connection rather than the pooled runtime URL.
unpooled_database_url = os.environ.get("DATABASE_URL_UNPOOLED")
if unpooled_database_url:
    os.environ["DATABASE_URL"] = unpooled_database_url

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.preview")

import django  # noqa: E402
from django.core.management import call_command  # noqa: E402


def main():
    django.setup()
    call_command("migrate", interactive=False)
    call_command("createcachetable", interactive=False)
    call_command("seed_demo_data")
    call_command("collectstatic", interactive=False)


if __name__ == "__main__":
    main()
