from .base import *  # noqa: F403,F401

DEBUG = False
ALLOW_DEMO_DATA = True

# Vercel preview deployments receive unique *.vercel.app hostnames. Keep this
# relaxed host/origin policy isolated from the real production settings.
ALLOWED_HOSTS = list(dict.fromkeys([*ALLOWED_HOSTS, ".vercel.app"]))  # noqa: F405
CSRF_TRUSTED_ORIGINS = list(  # noqa: F405
    dict.fromkeys([*CSRF_TRUSTED_ORIGINS, "https://*.vercel.app"])
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 0

# The preview environment is intentionally self-contained. DatabaseCache keeps
# OTP/rate-limit state shared across serverless instances without requiring the
# production Redis service.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "preview_cache",
    }
}
