from .base import BASE_DIR, env


# ----------------------------------------
# Database
# ----------------------------------------

# Основная база данных проекта
# Используется пул соединений (через psycopg-pool)
DATABASES = {
    "default": {
        **env.db("DATABASE_URL"),
        "OPTIONS": {
            "pool": {
                "min_size": 4,
                "max_size": 16,
                "timeout": 5,
            }
        },
    }
}


# ----------------------------------------
# S3 Beget Storage
# ----------------------------------------

# Настройки для работы с S3 (Beget)
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")

# URL и протокол
AWS_S3_ENDPOINT_URL = "https://s3.ru1.storage.beget.cloud"
AWS_S3_USE_SSL = True

# Настройки поведения при перезаписи файлов
AWS_S3_FILE_OVERWRITE = True
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False

# Конфигурация storage backends
STORAGES = {
    # медиа
    "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
    # статика
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# URL для медиа-файлов, доступных через S3
MEDIA_URL = f"https://s3.ru1.storage.beget.cloud/{AWS_STORAGE_BUCKET_NAME}/"


# ----------------------------------------
# Static и Media
# ----------------------------------------

# URL для статических файлов
STATIC_URL = "static/"

# Дополнительные директории для статических файлов проекта
STATICFILES_DIRS = [BASE_DIR / "static"]

# Директория для collectstatic
STATIC_ROOT = BASE_DIR / "staticfiles"

# Статика через WhiteNoise
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Директория для загружаемых пользователями медиа-файлов (локально)
MEDIA_ROOT = BASE_DIR / "media"
