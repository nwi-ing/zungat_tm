from datetime import datetime, timezone

import pytest

from apps.domain.autopayment.application.autopayment2 import AutopaymentApplication
from apps.integrations.bx24.lib.schemas import Deal, PaymentRule, PaymentRuleState
from apps.integrations.tm_driver.lib.schemas import Driver

pytestmark = pytest.mark.django_db

TODAY = datetime.now(timezone.utc).date().isoformat()


def test_autopayment_application_runs_end_to_end_without_crashing(fake_bx_client, fake_tm_client):
    # Раньше execute() падал с AttributeError/TypeError на предпоследней и
    # последней строчках — это регрессионный тест на оба бага сразу.
    fake_bx_client.deal.add(Deal(id=1, opportunity=5000, total_arest_sum=0, installment_pay_sum=0))
    fake_bx_client.payment_rule.add(
        PaymentRule(
            id=10, deal_id=1, driver_id=10606,
            is_active=PaymentRuleState.SCHEDULED,
            payment_sum=1000, first_pay_date=TODAY, last_payment_date=None,
            payment_frequency=175,
        )
    )
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=10000))

    installments = AutopaymentApplication(bx_client=fake_bx_client, tm_client=fake_tm_client).execute()

    payments = fake_bx_client.fact_payment.list()
    assert len(payments) == 1
    assert payments[0].opportunity == 1000
    assert payments[0].tm_payment_id is not None

    # execute() возвращает список успешно созданных installment -- это то,
    # что читает Celery-задача для построения детального лога по платежам.
    assert len(installments) == 1
    assert installments[0].fact_payment.id == payments[0].id
    assert installments[0].payment_rule.driver_id == 10606
