import logging.config
import os

from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger

from studyoverflow import settings


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studyoverflow.settings")

app = Celery("studyoverflow")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "sync_online_users_every_1_min": {
        "task": "users.tasks.sync_online_users_to_db",
        "schedule": 60,
    },
    "sync_user_activity_counters_every_1_min": {
        "task": "users.tasks.sync_user_activity_counters",
        "schedule": 60,
        "kwargs": {"batch_size": 1000},
    },
    "sync_post_counters_every_1_min": {
        "task": "posts.tasks.sync_post_counters",
        "schedule": 60,
    },
    "sync_comment_counters_every_1_min": {
        "task": "posts.tasks.sync_comment_counters",
        "schedule": 60,
    },
    "clear_expired_sessions": {
        "task": "users.tasks.clear_expired_sessions",
        "schedule": 60,  # crontab(hour=3, minute=0) - каждый день в 3 часа ночи
    },
    "flush_expired_jwt_tokens": {
        "task": "users.tasks.flush_expired_jwt_tokens",
        "schedule": 60,  # crontab(hour=3, minute=0) - каждый день в 3 часа ночи
    },
}


@after_setup_logger.connect
@after_setup_task_logger.connect
def setup_loggers(logger, *args, **kwargs):
    logging.config.dictConfig(settings.LOGGING)
