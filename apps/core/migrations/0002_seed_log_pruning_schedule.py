from django.db import migrations


def seed(apps, schema_editor):
    CrontabSchedule = apps.get_model("django_celery_beat", "CrontabSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="3",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        timezone="Europe/Moscow",
    )
    PeriodicTask.objects.get_or_create(
        task="core.prune_old_logs",
        defaults={"name": "core: очистка старых логов", "crontab": schedule, "enabled": True},
    )


def unseed(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(task="core.prune_old_logs").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        # need the final migration, not just 0001 — CrontabSchedule.timezone
        # is added later (0016_alter_crontabschedule_timezone)
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
