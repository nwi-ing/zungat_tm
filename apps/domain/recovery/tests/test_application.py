import pytest

from apps.domain.recovery.application.recovery import RecoveryApplication
from apps.domain.recovery.models import DriverSyncState
from apps.integrations.bx24.lib.schemas import Deal, PaymentRule, PaymentRuleState
from apps.integrations.tm_driver.lib.schemas import Operation

pytestmark = pytest.mark.django_db


def test_recovery_application_creates_fact_payment_and_advances_watermark(fake_bx_client, fake_tm_client):
    fake_bx_client.deal.add(Deal(id=1, title="Рассрочка №1", total_arest_sum=400))
    fake_bx_client.payment_rule.add(
        PaymentRule(id=10, deal_id=1, driver_id=10606, is_active=PaymentRuleState.SCHEDULED)
    )
    receipt = fake_tm_client.operation.seed(
        Operation(driver_id=10606, sum=1000, oper_type="receipt", title="Пополнение",
                  cancelled_oper_id=0, cancelled_by_oper_id=0)
    )

    RecoveryApplication(bx_client=fake_bx_client, tm_client=fake_tm_client).execute()

    payments = fake_bx_client.fact_payment.list()
    assert len(payments) == 1
    assert payments[0].opportunity == 400
    assert payments[0].deal_id == 1

    sync_state = DriverSyncState.objects.get(driver_id=10606)
    assert sync_state.last_processed_operation_id == receipt.id


def test_recovery_application_noop_when_no_receipts(fake_bx_client, fake_tm_client):
    fake_bx_client.deal.add(Deal(id=1, title="Рассрочка №1", total_arest_sum=400))
    fake_bx_client.payment_rule.add(
        PaymentRule(id=10, deal_id=1, driver_id=10606, is_active=PaymentRuleState.SCHEDULED)
    )

    RecoveryApplication(bx_client=fake_bx_client, tm_client=fake_tm_client).execute()

    assert fake_bx_client.fact_payment.list() == []
