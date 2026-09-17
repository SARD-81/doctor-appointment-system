"""Prepare the isolated Vercel preview environment during deployment."""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

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
    call_command("createcachetable")
    call_command("seed_demo_data")
    call_command("collectstatic", interactive=False)


if __name__ == "__main__":
    main()
