from django.db import migrations


def seed(apps, schema_editor):
    AutomationSetting = apps.get_model("core", "AutomationSetting")
    AutomationSetting.objects.get_or_create(
        module_key="autopayment",
        defaults={"label": "Автосписания по графику (autopayment)", "enabled": False},
    )

    CrontabSchedule = apps.get_model("django_celery_beat", "CrontabSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="22",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        timezone="Europe/Moscow",
    )
    PeriodicTask.objects.get_or_create(
        task="core.autopayment",
        defaults={"name": "autopayment: автосписания по графику", "crontab": schedule, "enabled": True},
    )


def unseed(apps, schema_editor):
    AutomationSetting = apps.get_model("core", "AutomationSetting")
    AutomationSetting.objects.filter(module_key="autopayment").delete()

    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(task="core.autopayment").delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_initial"),
        # need the final migration, not just 0001 — CrontabSchedule.timezone
        # is added later (0016_alter_crontabschedule_timezone)
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
