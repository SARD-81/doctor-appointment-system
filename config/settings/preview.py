from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403,F401

DEBUG = False
ALLOW_DEMO_DATA = True

# Vercel preview deployments receive unique *.vercel.app hostnames. Keep this
# relaxed host/origin policy isolated from the real production settings.
ALLOWED_HOSTS = list(
    dict.fromkeys(
        [
            *ALLOWED_HOSTS,  # noqa: F405
            ".vercel.app",
        ]
    )
)
CSRF_TRUSTED_ORIGINS = list(
    dict.fromkeys(
        [
            *CSRF_TRUSTED_ORIGINS,  # noqa: F405
            "https://*.vercel.app",
        ]
    )
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

# Public preview users must receive OTP and booking emails for real. The preview
# defaults target Resend SMTP, while every value can still be overridden through
# Vercel environment variables if a different SMTP provider is used later.
EMAIL_BACKEND = env(  # noqa: F405
    "EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="smtp.resend.com")  # noqa: F405
EMAIL_PORT = env.int("EMAIL_PORT", default=465)  # noqa: F405
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="resend")  # noqa: F405
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")  # noqa: F405
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)  # noqa: F405
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=True)  # noqa: F405
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=10)  # noqa: F405
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="")  # noqa: F405

if EMAIL_BACKEND != "django.core.mail.backends.smtp.EmailBackend":
    raise ImproperlyConfigured(
        "Vercel preview requires Django's SMTP email backend for real OTP delivery."
    )

if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ImproperlyConfigured(
        "Vercel preview email cannot enable EMAIL_USE_TLS and EMAIL_USE_SSL together."
    )

missing_email_settings = []
if not EMAIL_HOST_PASSWORD:
    missing_email_settings.append("EMAIL_HOST_PASSWORD")
if not DEFAULT_FROM_EMAIL:
    missing_email_settings.append("DEFAULT_FROM_EMAIL")

if missing_email_settings:
    missing = ", ".join(missing_email_settings)
    raise ImproperlyConfigured(
        f"Vercel preview requires real SMTP delivery; missing environment variable(s): {missing}."
    )
