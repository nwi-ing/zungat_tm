import time
from contextlib import contextmanager

from apps.core.models import LogEntry


@contextmanager
def log_run(module: str, **context):
    started_at = time.monotonic()
    try:
        yield
    except Exception as exc:
        duration_ms = int((time.monotonic() - started_at) * 1000)
        LogEntry.objects.create(
            module=module,
            level=LogEntry.Level.ERROR,
            message=str(exc),
            context={**context, "error_type": type(exc).__name__},
            duration_ms=duration_ms,
        )
        raise
    else:
        duration_ms = int((time.monotonic() - started_at) * 1000)
        LogEntry.objects.create(
            module=module,
            level=LogEntry.Level.INFO,
            message="OK",
            context=context,
            duration_ms=duration_ms,
        )
