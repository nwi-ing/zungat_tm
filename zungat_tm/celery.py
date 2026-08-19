import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zungat_tm.settings")

app = Celery("zungat_tm")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
