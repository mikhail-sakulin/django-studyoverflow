# ----------------------------------------
# Logging
# ----------------------------------------

# Конфигурация логирования проекта
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # Не отключать встроенные логгеры Django
    "formatters": {
        # Формат JSON для обычного логирования
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d",
        },
        # Формат JSON для Celery
        "json_celery": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "DEBUG",
        },
        "celery_console": {
            "class": "logging.StreamHandler",
            "formatter": "json_celery",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "django": {
            "handlers": [
                "console",
            ],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": [
                "console",
            ],
            "level": "INFO",
            "propagate": False,
        },
        "django.server": {
            "handlers": [
                "console",
            ],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": [
                "celery_console",
            ],
            "level": "INFO",
            "propagate": False,
        },
        "celery.task": {
            "handlers": [
                "celery_console",
            ],
            "level": "INFO",
            "propagate": False,
        },
        "studyoverflow": {
            "handlers": [
                "console",
            ],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    "root": {
        "handlers": [
            "console",
        ],
        "level": "INFO",
    },
}
