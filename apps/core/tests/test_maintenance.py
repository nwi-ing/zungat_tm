from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.models import LogEntry
from apps.core.tasks import prune_old_logs

pytestmark = pytest.mark.django_db


def test_prune_old_logs_deletes_entries_older_than_retention(settings):
    settings.LOG_RETENTION_DAYS = 30

    old = LogEntry.objects.create(module="smoke", message="old")
    LogEntry.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=31))

    recent = LogEntry.objects.create(module="smoke", message="recent")

    deleted = prune_old_logs()

    assert deleted == 1
    assert not LogEntry.objects.filter(pk=old.pk).exists()
    assert LogEntry.objects.filter(pk=recent.pk).exists()
