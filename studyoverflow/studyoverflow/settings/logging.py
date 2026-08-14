# ----------------------------------------
# Logging
# ----------------------------------------

# Конфигурация логирования проекта, используется стандартный модуль logging
#
# "propagate": False для логгеров отключает передачу сообщений от текущего логгера к его родителю
# по иерархии имен логгеров, False убирает дублирование логов.
LOGGING = {
    "version": 1,
    # Не отключать встроенные логгеры Django
    "disable_existing_loggers": False,
    "formatters": {
        # Формат JSON для обычного логирования
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            # JSON-форматтер из python-json-logger, формат задан для Loki/Grafana
            # s - переменная должна быть преобразована в строку, d - в целое число
            "format": "%(asctime)s "
            "%(levelname)s "
            "%(name)s "
            "%(message)s "
            "%(module)s "
            "%(funcName)s "
            "%(lineno)d",
            # Параметр сериализации JSON (отключает кодирование текста Unicode-символов в
            # кодировку ASCII), например, отключает принудительное кодирование кириллицы в ASCII.
            "json_ensure_ascii": False,
        },
        # Отдельный JSON-форматтер для Celery
        "json_celery": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "format": "%(asctime)s " "%(levelname)s " "%(name)s " "%(message)s",
            "json_ensure_ascii": False,
        },
    },
    "handlers": {
        "console": {
            # StreamHandler выводит сообщение в stderr, Promtail читает логи контейнеров
            # Docker и сохраняет логи в Loki, где их можно посмотреть через Grafana.
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "DEBUG",
        },
        # Отдельный handler для Celery с другим (более компактным) JSON-форматтером
        "celery_console": {
            "class": "logging.StreamHandler",
            "formatter": "json_celery",
            "level": "DEBUG",
        },
    },
    "loggers": {
        # Родительский логгер Django, ловит сообщения Django, которые не были обработаны
        # узконаправленными логгерами.
        # Логирует, например, статус применения миграций, ошибки внутри ядра Django,
        # результаты системной проверки при запуске и так далее.
        "django": {
            "handlers": [
                "console",
            ],
            "level": "INFO",
            "propagate": False,
        },
        # Отвечает за обработку входящих HTTP-запросов от клиентов,
        # которые завершились ошибками (статус-коды 500-ые и 400-ые).
        # Не логирует успешные ответы с кодами 100-ые, 200-ые и 300-ые.
        "django.request": {
            "handlers": [
                "console",
            ],
            "level": "INFO",
            "propagate": False,
        },
        # Логгер встроенного dev-сервера (manage.py runserver), логирует только
        # тестовый веб-сервер, например сообщение о запуске сервера, входящие запросы со всеми
        # кодами ответов. При использовании ASGI-сервера Daphne перестает что-либо
        # логировать.
        #
        # На данный момент в dev используется:
        #     command: python manage.py runserver 0.0.0.0:8000, но
        # также указан "daphne" в INSTALLED_APPS, поэтому тестовый веб-сервер не используется,
        # вместо "django.server" отрабатывает логгер "django.channels.server", который сейчас
        # не задан, поэтому логи обработаются логгером "django" по иерархии.
        "django.server": {
            "handlers": [
                "console",
            ],
            "level": "INFO",
            "propagate": False,
        },
        #
        #
        # Логгера входящих соединений ASGI-сервера Daphne для prod нет, поскольку в prod при
        # запуске приложения через ASGI-сервер Daphne как
        #     daphne --proxy-headers -b 0.0.0.0 -p 8000 studyoverflow.asgi:application
        # запросы по протоколам HTTP и WebSocket не логируются, а записи запросов
        # пишутся в sys.stdout напрямую в обход модуля logging.
        #
        # В dev режиме (описано в комментариях логгера "django.server") запросы уже логируются
        # ASGI-сервером Daphne через "django.channels.server".
        #
        #
        # Отвечает за техническое состояние самого сервера Daphne, не имеет отношения к клиентам
        # Логирует запуск сервера и привязку к портам, остановку или падение сервера.
        "daphne.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # Родительский логгер для Celery. Обрабатывает сообщения от Celery и его дочерних
        # логгеров, например от celery.task (логирует жизненный цикл каждой Celery-задачи).
        "celery": {
            "handlers": [
                "celery_console",
            ],
            "level": "INFO",
            "propagate": False,
        },
        # Кастомный логгер, с уровнем логирования "DEBUG", сейчас в проекте не используется,
        # так как при запуске бекенда из studyoverflow директории имена логгеров становятся,
        # например, "name": "posts.services.loggers". Для обработки таких логов используется
        # root логгер.
        "studyoverflow": {
            "handlers": [
                "console",
            ],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    # Корневой логгер, если какой-либо лог, например из сторонней библиотеки, не будет обработан
    # каким-либо заданным выше логгером, то лог обработается логгером "root"
    "root": {
        "handlers": [
            "console",
        ],
        "level": "INFO",
    },
    # Логирует SQL-запросы, генерируемые только на уровне DEBUG,
    # в проекте не используется.
    # "django.db.backends": {
    #     "handlers": ["console"],
    #     # Уровень нужен именно "DEBUG" для SQL-запросов
    #     "level": "DEBUG",
    #     "propagate": False,
    # }
}
