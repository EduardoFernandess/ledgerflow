from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Prefer Redis when available; fall back for bare-metal local runs without Redis.
try:
    import redis

    redis.Redis.from_url(REDIS_URL).ping()  # noqa: F405
except Exception:
    CACHES = {  # noqa: F405
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "ledgerflow-local",
        }
    }
