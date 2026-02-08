from .base import TIME_ZONE, env


# --- Celery ------------------------------------------------------------------

# URL брокера сообщений
CELERY_BROKER_URL = env("CELERY_BROKER_URL")

# Backend для хранения результатов задач Celery
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")

# Часовой пояс Celery
CELERY_TIMEZONE = TIME_ZONE


# ---  Channels with Redis ----------------------------------------------------

# Конфигурация Django Channels через Redis
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_CHANNELS_URL")],
        },
    },
}


# --- Celery Once -------------------------------------------------------------

# Настройки celery-once (для предотвращения дублирования задач)
CELERY_ONCE = {
    "backend": "celery_once.backends.Redis",
    "settings": {
        "url": env("REDIS_CELERY_ONCE_URL"),
        "default_timeout": 10,
    },
}


# --- Cache (Redis) ------------------------------------------------------------

# Настройка кеша через django-redis
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_CACHE_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "studyoverflow",
    }
}
