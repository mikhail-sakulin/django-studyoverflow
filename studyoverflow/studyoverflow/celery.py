import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studyoverflow.settings")

app = Celery("studyoverflow")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
