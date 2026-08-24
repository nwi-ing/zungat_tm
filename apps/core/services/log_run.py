import time
from contextlib import contextmanager

from apps.core.models import LogEntry, PaymentLogEntry


def _attach_payments(entry, payments):
    if not payments:
        return
    PaymentLogEntry.objects.bulk_create(
        PaymentLogEntry(
            log_entry=entry,
            driver_id=p.get("driver_id"),
            deal_id=p.get("deal_id"),
            fact_payment_id=p.get("fact_payment_id"),
            amount=p.get("amount"),
            arrest_amount=p.get("arrest_amount"),
            success=p.get("success", True),
            error_message=p.get("error_message", ""),
        )
        for p in payments
    )


@contextmanager
def log_run(module: str, **context):
    """Контекст-менеджер: одна LogEntry на запуск. Через yield отдаёт
    изменяемый словарь — вызывающий код может положить в ctx["payments"]
    список платежей (dict с driver_id/deal_id/fact_payment_id/amount/...),
    они сохранятся как дочерние PaymentLogEntry."""
    started_at = time.monotonic()
    ctx = dict(context)
    try:
        yield ctx
    except Exception as exc:
        duration_ms = int((time.monotonic() - started_at) * 1000)
        payments = ctx.pop("payments", None)
        entry = LogEntry.objects.create(
            module=module,
            level=LogEntry.Level.ERROR,
            message=str(exc),
            context={**ctx, "error_type": type(exc).__name__},
            duration_ms=duration_ms,
        )
        _attach_payments(entry, payments)
        raise
    else:
        duration_ms = int((time.monotonic() - started_at) * 1000)
        payments = ctx.pop("payments", None)
        message = f"OK: {len(payments)} платежей" if payments else "OK"
        entry = LogEntry.objects.create(
            module=module,
            level=LogEntry.Level.INFO,
            message=message,
            context=ctx,
            duration_ms=duration_ms,
        )
        _attach_payments(entry, payments)
