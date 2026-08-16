from .base import BASE_DIR, env


# ----------------------------------------
# Database
# ----------------------------------------

# По умолчанию пул соединений к БД включен. Для процесса, где используется celery --pool=gevent
# (зеленые потоки) (celery worker в prod-lite и cd-lite), пул отключается через переменную
# окружения, так как psycopg-pool несовместим с gevent monkey-patching.
DB_USE_POOL = env.bool("DB_USE_POOL", default=True)

db_options = {}

if DB_USE_POOL:
    db_options["pool"] = {
        "min_size": 4,
        "max_size": 16,
        "timeout": 5,
    }

# База данных проекта.
# Если не задано DB_USE_POOL == False, то используется пул соединений (через psycopg-pool),
# пул привязан к 1 процессу.
DATABASES = {
    "default": {
        # **env.db("DATABASE_URL"),
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
        # 1) CONN_MAX_AGE - сколько живет соединение с БД, которое можно переиспользовать,
        # по истечении срока соединение закрывается и открывается новое. Если задано
        # значение 0, то соединение закрывается сразу после использования (не ждет),
        # при int - существует указанное число секунд, при None - соединение существует,
        # пока с ним что-то не случится.
        # 2) Без пула соединение к БД привязано к потоку ОС, даже если CONN_MAX_AGE не истек,
        # то другой поток не сможет переиспользовать соединение. С пулом соединений каждое
        # соединение уже привязано к процессу, а не к потоку ОС.
        # 3) Задается либо "CONN_MAX_AGE", либо пул соединений к БД.
        "CONN_MAX_AGE": 0 if DB_USE_POOL else 60,
        "OPTIONS": db_options,
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

# Кастомный домен S3 (Beget), который используется для генерации ссылок на файлы в S3
AWS_S3_CUSTOM_DOMAIN = f"s3.ru1.storage.beget.cloud/{AWS_STORAGE_BUCKET_NAME}"

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
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Директория для загружаемых пользователями медиа-файлов (локально)
MEDIA_ROOT = BASE_DIR / "media"
