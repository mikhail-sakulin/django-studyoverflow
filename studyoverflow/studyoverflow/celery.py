import logging.config
import os

from celery import Celery
from celery.schedules import crontab
from celery.signals import after_setup_logger, after_setup_task_logger
from django.conf import settings


# Задает переменную окружения со значением "studyoverflow.settings", если она не была задана ранее,
# данная переменная окружения нужна внутренним механизмам Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studyoverflow.settings")

# Экземпляр celery-приложения, задается имя "studyoverflow"
app = Celery("studyoverflow")

# Указывается, что настройки Celery лежат в settings.py (from django.conf import settings) и
# начинаются с префикса CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Celery автоматически просматривает список INSTALLED_APPS и импортирует все функции с декораторами
# @shared_task или @app.task из файлов tasks.py. Имя переменной INSTALLED_APPS задано
# в коде библиотеки Celery.
app.autodiscover_tasks()

# Определение расписания для периодических задач.
app.conf.beat_schedule = {
    "sync_online_users_to_db": {
        "task": "users.tasks.sync_online_users_to_db",
        # Задача запускается каждые 60 секунд
        "schedule": 60,
    },
    "sync_user_activity_counters": {
        "task": "users.tasks.sync_user_activity_counters",
        # Задача запускается каждый день в 3 часа ночи
        "schedule": crontab(hour=3, minute=0),
        "kwargs": {"batch_size": 1000},
    },
    "sync_post_counters": {
        "task": "posts.tasks.sync_post_counters",
        "schedule": crontab(hour=3, minute=30),
    },
    "sync_comment_counters": {
        "task": "posts.tasks.sync_comment_counters",
        "schedule": crontab(hour=4, minute=0),
    },
    "clear_expired_sessions": {
        "task": "users.tasks.clear_expired_sessions",
        "schedule": crontab(hour=4, minute=30),
    },
    "flush_expired_jwt_tokens": {
        "task": "users.tasks.flush_expired_jwt_tokens",
        "schedule": crontab(hour=5, minute=0),
    },
}


# По умолчанию Celery игнорирует настройки логов Django и использует свой формат.
# Эти настройки заставляют celery применять формат логов из настроек Django.
# after_setup_logger - сигнал срабатывает, когда Celery настроил системный логгер (для вывода лога,
# что воркер запущен и так далее);
# after_setup_task_logger - сигнал срабатывает, когда Celery настроил логгер для задач
# .connect - функция setup_loggers запускается после того, как Celery закончил настраивать
# логгеры по умолчанию
@after_setup_logger.connect
@after_setup_task_logger.connect
def setup_loggers(logger, *args, **kwargs):
    # Перезаписывает настройки логирования в Celery процессе настройками из settings.LOGGING
    logging.config.dictConfig(settings.LOGGING)
