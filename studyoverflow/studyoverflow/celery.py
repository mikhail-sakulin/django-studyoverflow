import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studyoverflow.settings")

app = Celery("studyoverflow")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "sync_online_users_every_1_min": {
        "task": "users.tasks.sync_online_users_to_db",
        "schedule": 60,
    }
}
