import functools

from celery import shared_task

from apps.core.models import LogEntry
from apps.core.services import is_module_enabled, log_run


def automation_task(module_key: str):
    """Celery task decorator: gates execution on AutomationSetting.enabled
    and records exactly one LogEntry per run. The wrapped function itself
    (an Application.execute()) stays unaware of gating/logging."""

    def decorator(func):
        @shared_task(name=f"core.{module_key}")
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not is_module_enabled(module_key):
                LogEntry.objects.create(
                    module=module_key,
                    level=LogEntry.Level.INFO,
                    message="skipped: disabled",
                )
                return None
            with log_run(module_key) as ctx:
                return func(ctx, *args, **kwargs)

        return wrapper

    return decorator
