import pytest

from apps.domain.autopayment.schemas.installment import Installment
from apps.domain.autopayment.services import CreatePayment
from apps.integrations.bx24.lib.schemas import Deal, FactPayment, PaymentRule
from apps.integrations.tm_driver.lib.schemas import Operation

pytestmark = pytest.mark.django_db


def make_installment():
    return Installment(
        payment_rule=PaymentRule(id=1, deal_id=1, driver_id=10606),
        deal=Deal(id=1),
        operation=Operation(id=555, driver_id=10606, oper_sum=500, oper_type="expense"),
        fact_payment=FactPayment(deal_id=1, opportunity=500, arest_sum=0),
    )


def test_create_links_tm_operation_id_and_returns_installment(fake_bx_client):
    installment = make_installment()

    result = CreatePayment(fake_bx_client).create([installment])

    assert len(result) == 1
    assert result[0].fact_payment.tm_payment_id == 555
    assert fake_bx_client.fact_payment.list() != []


def test_create_skips_installment_on_bx_failure_instead_of_crashing(fake_bx_client, monkeypatch):
    installment = make_installment()

    def _boom(obj):
        raise RuntimeError("Bitrix недоступен")

    monkeypatch.setattr(fake_bx_client.fact_payment, "add", _boom)

    # раньше здесь падал UnboundLocalError вместо аккуратного пропуска
    result = CreatePayment(fake_bx_client).create([installment])

    assert result == []
