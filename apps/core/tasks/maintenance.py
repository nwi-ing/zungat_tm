from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.core.models import LogEntry


@shared_task(name="core.prune_old_logs")
def prune_old_logs():
    cutoff = timezone.now() - timedelta(days=settings.LOG_RETENTION_DAYS)
    deleted, _ = LogEntry.objects.filter(created_at__lt=cutoff).delete()
    return deleted
