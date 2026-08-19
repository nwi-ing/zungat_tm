import pytest

from apps.domain._shared.services import DataNotFoundError, PaymentContextLoader
from apps.integrations.bx24.lib.schemas import Deal, FactPayment, PaymentRule

pytestmark = pytest.mark.django_db


def test_load_chains_payment_deal_and_payment_rule(fake_bx_client):
    fake_bx_client.deal.add(Deal(id=1, payment_rule=10))
    fake_bx_client.payment_rule.add(PaymentRule(id=10, deal_id=1))
    fake_bx_client.fact_payment.add(FactPayment(id=100, deal_id=1))

    fact_payment, deal, payment_rule = PaymentContextLoader(fake_bx_client).load(100)

    assert fact_payment.id == 100
    assert deal.id == 1
    assert payment_rule.id == 10


def test_missing_fact_payment_raises_not_found(fake_bx_client):
    with pytest.raises(DataNotFoundError):
        PaymentContextLoader(fake_bx_client).load(999)


def test_missing_deal_id_raises_not_found(fake_bx_client):
    fake_bx_client.fact_payment.add(FactPayment(id=100, deal_id=None))
    with pytest.raises(DataNotFoundError):
        PaymentContextLoader(fake_bx_client).load(100)


def test_missing_payment_rule_id_raises_not_found(fake_bx_client):
    fake_bx_client.deal.add(Deal(id=1, payment_rule=None))
    fake_bx_client.fact_payment.add(FactPayment(id=100, deal_id=1))
    with pytest.raises(DataNotFoundError):
        PaymentContextLoader(fake_bx_client).load(100)
