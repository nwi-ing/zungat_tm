import pytest

from apps.core.models import AutomationSetting, LogEntry, PaymentLogEntry
from apps.core.services import is_module_enabled, log_run
from apps.core.tasks import automation_task
from apps.integrations.bx24.lib.schemas import Deal
from apps.integrations.tm_driver.lib.schemas import Driver
from zungat_tm.celery import app as celery_app

pytestmark = pytest.mark.django_db


def test_celery_app_created():
    assert celery_app.main == "zungat_tm"


def test_log_run_creates_one_entry_on_success():
    with log_run("smoke", driver_id=1):
        pass
    entry = LogEntry.objects.get()
    assert entry.module == "smoke"
    assert entry.level == LogEntry.Level.INFO
    assert entry.context == {"driver_id": 1}


def test_log_run_logs_error_and_reraises():
    with pytest.raises(ValueError):
        with log_run("smoke"):
            raise ValueError("boom")
    entry = LogEntry.objects.get()
    assert entry.level == LogEntry.Level.ERROR
    assert "boom" in entry.message


def test_is_module_enabled_respects_flag():
    AutomationSetting.objects.create(module_key="smoke", enabled=False)
    assert is_module_enabled("smoke") is False


def test_log_run_attaches_payment_log_entries():
    with log_run("smoke") as ctx:
        ctx["payments"] = [
            {"driver_id": 10606, "deal_id": 1, "fact_payment_id": 555, "amount": 200.0, "success": True},
            {"driver_id": 999, "deal_id": 2, "amount": None, "success": False, "error_message": "boom"},
        ]
    entry = LogEntry.objects.get()
    assert entry.message == "OK: 2 платежей"
    assert "payments" not in entry.context

    rows = list(PaymentLogEntry.objects.filter(log_entry=entry).order_by("driver_id"))
    assert len(rows) == 2
    assert rows[0].driver_id == 999
    assert rows[0].success is False
    assert rows[0].error_message == "boom"
    assert rows[1].driver_id == 10606
    assert rows[1].fact_payment_id == 555
    assert rows[1].amount == 200.0


def test_log_run_without_payments_leaves_no_child_rows():
    with log_run("smoke"):
        pass
    entry = LogEntry.objects.get()
    assert entry.message == "OK"
    assert PaymentLogEntry.objects.filter(log_entry=entry).count() == 0


def test_automation_task_skips_when_disabled():
    calls = []

    @automation_task(module_key="smoke_task")
    def run():
        calls.append(1)

    AutomationSetting.objects.create(module_key="smoke_task", enabled=False)
    run()

    assert calls == []
    entry = LogEntry.objects.get()
    assert entry.message == "skipped: disabled"


def test_automation_task_runs_and_logs_when_enabled():
    calls = []

    @automation_task(module_key="smoke_task2")
    def run(ctx):
        calls.append(1)

    AutomationSetting.objects.create(module_key="smoke_task2", enabled=True)
    run()

    assert calls == [1]
    entry = LogEntry.objects.get()
    assert entry.level == LogEntry.Level.INFO
    assert entry.message == "OK"


def test_fake_bx_client_seeds_and_filters(fake_bx_client):
    deal = fake_bx_client.deal.add(Deal(id=1, title="Рассрочка №1"))
    assert fake_bx_client.deal.get(1) == deal
    assert fake_bx_client.deal.list(filters={"id": [1, 2]}) == [deal]
    assert fake_bx_client.deal.list(filters={"id": [2]}) == []


def test_fake_tm_client_seeds_driver_and_operations(fake_tm_client):
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=100.0))
    driver = fake_tm_client.driver.get(10606)
    assert driver.balance == 100.0

    from apps.integrations.tm_driver.lib.schemas import Operation

    fake_tm_client.operation.seed(Operation(driver_id=10606, sum=500, oper_type="receipt"))
    ops = fake_tm_client.operation.get(driver_id=10606, start_time=None, finish_time=None)
    assert len(ops) == 1
    assert ops[0].id is not None
