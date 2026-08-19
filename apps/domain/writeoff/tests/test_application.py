import pytest

from apps.domain.writeoff.application.manual_writeoff import ManualWriteoffApplication
from apps.integrations.bx24.lib.schemas import Deal, FactPayment, PaymentRule
from apps.integrations.tm_driver.lib.schemas import Driver

pytestmark = pytest.mark.django_db


def seed_context(fake_bx_client):
    fake_bx_client.payment_rule.add(PaymentRule(id=10, deal_id=1, driver_id=10606, allow_overdraft=True))
    fake_bx_client.deal.add(Deal(id=1, payment_rule=10, opportunity=5000, total_arest_sum=0, installment_pay_sum=0))
    fake_bx_client.fact_payment.add(
        FactPayment(
            id=100, deal_id=1, opportunity=500,
            payment_type_id=255, payment_state_id=289, cenceled_tm_payment_id=None,
        )
    )


def test_writeoff_happy_path_creates_expense_and_updates_bitrix(fake_bx_client, fake_tm_client):
    seed_context(fake_bx_client)
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=1000))

    ManualWriteoffApplication(bx_client=fake_bx_client, tm_client=fake_tm_client).execute(fact_payment_id=100)

    ops = fake_tm_client.operation.get(driver_id=10606, start_time=None, finish_time=None)
    assert len(ops) == 1
    assert ops[0].oper_type == "expense"
    assert ops[0].oper_sum == 500

    updated = fake_bx_client.fact_payment.get(100)
    assert updated.stage_id == "DT1052_15:SUCCESS"
    assert updated.opportunity == 500
    assert updated.arest_sum == 0

    messages = [m.title for m in fake_bx_client.fact_payment.timeline.messages]
    assert "Обработка платежа" in messages
    assert "Успешный платеж" in messages


def test_writeoff_rolls_back_on_validation_error(fake_bx_client, fake_tm_client):
    seed_context(fake_bx_client)
    fake_bx_client.fact_payment.update(FactPayment(id=100, payment_state_id=285, previous_stage_id="OLD_STAGE"))
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=1000))

    ManualWriteoffApplication(bx_client=fake_bx_client, tm_client=fake_tm_client).execute(fact_payment_id=100)

    updated = fake_bx_client.fact_payment.get(100)
    assert updated.stage_id == "OLD_STAGE"

    messages = [m.title for m in fake_bx_client.fact_payment.timeline.messages]
    assert "Ошибка списания денег" in messages
