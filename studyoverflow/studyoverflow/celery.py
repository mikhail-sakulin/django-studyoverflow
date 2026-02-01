import logging.config
import os

from celery import Celery
from celery.schedules import crontab
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
        "schedule": crontab(minute=0),
        "kwargs": {"batch_size": 1000},
    },
}


@after_setup_logger.connect
@after_setup_task_logger.connect
def setup_loggers(logger, *args, **kwargs):
    logging.config.dictConfig(settings.LOGGING)
