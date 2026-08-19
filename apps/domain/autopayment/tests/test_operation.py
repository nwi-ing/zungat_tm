import pytest

from apps.domain.autopayment.schemas.installment import Installment
from apps.domain.autopayment.services import MakeOperation
from apps.integrations.bx24.lib.schemas import Deal, PaymentRule
from apps.integrations.tm_driver.lib.schemas import Operation

pytestmark = pytest.mark.django_db


def test_make_creates_tm_operation_and_assigns_id(fake_tm_client):
    installment = Installment(
        payment_rule=PaymentRule(id=1, deal_id=1, driver_id=10606),
        deal=Deal(id=1, title="Рассрочка №1"),
        operation=Operation(driver_id=10606, oper_sum=500, oper_type="expense", title="Автоматическое списание. Зунгат"),
    )

    result = MakeOperation(fake_tm_client).make([installment])

    assert result[0].operation.id is not None
    assert fake_tm_client.operation.get(driver_id=10606, start_time=None, finish_time=None)[0].oper_sum == 500
