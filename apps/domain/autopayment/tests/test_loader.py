import pytest

from apps.domain.autopayment.services import InstallmentLoader
from apps.integrations.bx24.lib.schemas import Deal, PaymentRule

pytestmark = pytest.mark.django_db


def test_matches_deal_to_payment_rule_by_deal_id(fake_bx_client):
    fake_bx_client.deal.add(Deal(id=1, title="Рассрочка №1"))
    fake_bx_client.payment_rule.add(PaymentRule(id=10, deal_id=1, driver_id=10606))

    installments = InstallmentLoader(fake_bx_client).load()

    assert len(installments) == 1
    assert installments[0].deal.id == 1
    assert installments[0].payment_rule.id == 10


def test_installment_without_matching_deal_has_deal_none(fake_bx_client):
    fake_bx_client.payment_rule.add(PaymentRule(id=10, deal_id=999, driver_id=10606))

    installments = InstallmentLoader(fake_bx_client).load()

    assert len(installments) == 1
    assert installments[0].deal is None
