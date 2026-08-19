import pytest

from apps.domain.writeoff.services import PaymentValidator, ValidationError
from apps.integrations.bx24.lib.schemas import Deal, FactPayment, PaymentRule


def make_context(**fp_overrides):
    fields = dict(
        opportunity=500,
        payment_type_id=255,
        payment_state_id=289,
        cenceled_tm_payment_id=None,
    )
    fields.update(fp_overrides)
    fact_payment = FactPayment(**fields)
    deal = Deal(id=1, opportunity=5000, total_arest_sum=0, installment_pay_sum=0)
    payment_rule = PaymentRule(driver_id=10606)
    return fact_payment, deal, payment_rule


def test_valid_payment_passes():
    PaymentValidator(None).validate(*make_context())


def test_wrong_payment_type_is_rejected():
    fact_payment, deal, payment_rule = make_context(payment_type_id=253)
    with pytest.raises(ValidationError):
        PaymentValidator(None).validate(fact_payment, deal, payment_rule)


def test_already_processed_payment_is_rejected():
    fact_payment, deal, payment_rule = make_context(payment_state_id=285)
    with pytest.raises(ValidationError):
        PaymentValidator(None).validate(fact_payment, deal, payment_rule)


def test_already_cancelled_payment_is_rejected():
    fact_payment, deal, payment_rule = make_context(cenceled_tm_payment_id=999)
    with pytest.raises(ValidationError):
        PaymentValidator(None).validate(fact_payment, deal, payment_rule)


def test_sum_exceeding_deal_opportunity_is_rejected():
    fact_payment, deal, payment_rule = make_context(opportunity=6000)
    with pytest.raises(ValidationError):
        PaymentValidator(None).validate(fact_payment, deal, payment_rule)


def test_missing_driver_id_is_rejected():
    fact_payment, deal, _ = make_context()
    payment_rule = PaymentRule(driver_id=None)
    with pytest.raises(ValidationError):
        PaymentValidator(None).validate(fact_payment, deal, payment_rule)
