import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.core.models import AutomationSetting, LogEntry, PaymentLogEntry

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff_client(client):
    User = get_user_model()
    user = User.objects.create_user(username="staff", password="pass", is_staff=True)
    client.force_login(user)
    return client


def test_logs_page_renders(staff_client):
    response = staff_client.get(reverse("core:log_list"))
    assert response.status_code == 200
    assert "Логи" in response.content.decode()


def test_logs_page_requires_staff(client):
    response = client.get(reverse("core:log_list"))
    assert response.status_code == 302


def test_log_payments_shows_driver_and_amount(staff_client):
    entry = LogEntry.objects.create(module="recovery", level=LogEntry.Level.INFO, message="OK: 1 платежей")
    PaymentLogEntry.objects.create(log_entry=entry, driver_id=10606, deal_id=1, fact_payment_id=555, amount=400.0)

    response = staff_client.get(reverse("core:log_payments", args=[entry.id]))

    assert response.status_code == 200
    body = response.content.decode()
    assert "10606" in body
    assert "400" in body


def test_log_payments_requires_staff(client):
    entry = LogEntry.objects.create(module="recovery", level=LogEntry.Level.INFO, message="OK")
    response = client.get(reverse("core:log_payments", args=[entry.id]))
    assert response.status_code == 302


def test_settings_page_renders_and_toggles(staff_client):
    setting = AutomationSetting.objects.create(module_key="smoke_module", label="Smoke Module", enabled=False)
    response = staff_client.get(reverse("core:settings_panel"))
    assert response.status_code == 200
    assert "Smoke Module" in response.content.decode()

    response = staff_client.post(reverse("core:toggle_setting", args=["smoke_module"]))
    assert response.status_code == 200
    setting.refresh_from_db()
    assert setting.enabled is True
    assert "Включено" in response.content.decode()
