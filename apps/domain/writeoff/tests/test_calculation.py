import pytest

from apps.domain.writeoff.services import CalculateError, PaymentCalculation
from apps.integrations.bx24.lib.schemas import FactPayment, PaymentRule
from apps.integrations.tm_driver.lib.schemas import Driver

pytestmark = pytest.mark.django_db


def test_full_balance_covers_the_payment(fake_tm_client):
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=1000))
    fact_payment = FactPayment(opportunity=500)
    payment_rule = PaymentRule(driver_id=10606)

    paid, arrest = PaymentCalculation(fake_tm_client).calculate(fact_payment, payment_rule)

    assert (paid, arrest) == (500, 0)


def test_insufficient_balance_splits_paid_and_arrest_when_overdraft_allowed(fake_tm_client):
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=300))
    fact_payment = FactPayment(opportunity=1000)
    payment_rule = PaymentRule(driver_id=10606, allow_overdraft=True)

    paid, arrest = PaymentCalculation(fake_tm_client).calculate(fact_payment, payment_rule)

    assert (paid, arrest) == (300, 700)


def test_insufficient_balance_raises_when_overdraft_disallowed(fake_tm_client):
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=300))
    fact_payment = FactPayment(opportunity=1000)
    payment_rule = PaymentRule(driver_id=10606, allow_overdraft=False)

    with pytest.raises(CalculateError):
        PaymentCalculation(fake_tm_client).calculate(fact_payment, payment_rule)
