from apps.domain.cencel_payment.services import PaymentCalculation
from apps.integrations.bx24.lib.schemas import FactPayment, PaymentRule


def test_calculate_sums_opportunity_and_arest_without_balance_check():
    fact_payment = FactPayment(id=1, opportunity=500, arest_sum=300)
    payment_rule = PaymentRule(id=1, driver_id=10606)

    # tm_client=None — если бы calculate() всё ещё читал баланс, тест бы упал
    result = PaymentCalculation(tm_client=None).calculate(fact_payment, payment_rule)

    assert result == 800


def test_calculate_handles_missing_arest_sum():
    fact_payment = FactPayment(id=1, opportunity=500, arest_sum=None)
    payment_rule = PaymentRule(id=1, driver_id=10606)

    result = PaymentCalculation(tm_client=None).calculate(fact_payment, payment_rule)

    assert result == 500
