import pytest

from apps.domain.cencel_payment.application.cencel_payment import CencelPaymentApplication
from apps.domain.cencel_payment.services import UpdatePayment, UpdatePaymentError
from apps.integrations.bx24.lib.schemas import Deal, FactPayment, PaymentRule
from apps.integrations.tm_driver.lib.schemas import Driver

pytestmark = pytest.mark.django_db


def seed_context(fake_bx_client):
    fake_bx_client.payment_rule.add(PaymentRule(id=10, deal_id=1, driver_id=10606))
    fake_bx_client.deal.add(Deal(id=1, payment_rule=10, category_id=19))
    fake_bx_client.fact_payment.add(
        FactPayment(id=100, deal_id=1, payment_state_id=285, tm_payment_id=555, opportunity=500, arest_sum=0)
    )


def test_cencel_payment_happy_path_creates_receipt_and_updates_bitrix(fake_bx_client, fake_tm_client):
    seed_context(fake_bx_client)
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=1000))

    CencelPaymentApplication(bx_client=fake_bx_client, tm_client=fake_tm_client).execute(fact_payment_id=100)

    ops = fake_tm_client.operation.get(driver_id=10606, start_time=None, finish_time=None)
    assert len(ops) == 1
    assert ops[0].oper_type == "receipt"
    assert ops[0].oper_sum == 500

    updated = fake_bx_client.fact_payment.get(100)
    assert updated.stage_id == "DT1052_15:UC_LE9QRK"
    assert updated.cenceled_tm_payment_id == 555

    messages = [m.title for m in fake_bx_client.fact_payment.timeline.messages]
    assert "Обработка платежа" in messages
    assert "Платеж отменен" in messages


def test_update_payment_error_is_caught_not_propagated(fake_bx_client, fake_tm_client, monkeypatch):
    # Раньше здесь стоял `except UnicodeDecodeError`, который никогда не
    # перехватывал реальную ошибку UpdatePaymentError — она улетала наружу
    # из execute() и падала на уровне вебхука. Проверяем, что теперь она
    # аккуратно перехватывается.
    seed_context(fake_bx_client)
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=1000))

    def _boom(self, fact_payment, operation, payment_rule):
        raise UpdatePaymentError("Bitrix недоступен")

    monkeypatch.setattr(UpdatePayment, "update", _boom)

    # не должно бросить исключение наружу
    CencelPaymentApplication(bx_client=fake_bx_client, tm_client=fake_tm_client).execute(fact_payment_id=100)

    messages = [m.title for m in fake_bx_client.fact_payment.timeline.messages]
    assert "Ошибка списания денег" in messages
