from datetime import datetime, timezone

import pytest

from apps.domain.autopayment.schemas.installment import Installment
from apps.domain.autopayment.services import InstallmentValidator
from apps.integrations.bx24.lib.schemas import Deal, PaymentRule, PaymentRuleState

TODAY = datetime.now(timezone.utc).date().isoformat()


def make_rule(**overrides):
    fields = dict(
        id=1,
        deal_id=1,
        driver_id=10606,
        is_active=PaymentRuleState.SCHEDULED,
        first_pay_date=TODAY,
        last_payment_date=None,
        payment_frequency=175,
    )
    fields.update(overrides)
    return PaymentRule(**fields)


def make_deal(**overrides):
    fields = dict(id=1, opportunity=10000, total_arest_sum=0, installment_pay_sum=0)
    fields.update(overrides)
    return Deal(**fields)


def test_installment_due_today_passes():
    installment = Installment(payment_rule=make_rule(), deal=make_deal())
    assert InstallmentValidator(None).validate([installment]) == [installment]


def test_installment_already_paid_today_is_not_due():
    installment = Installment(payment_rule=make_rule(last_payment_date=TODAY), deal=make_deal())
    assert InstallmentValidator(None).validate([installment]) == []


def test_installment_with_inactive_rule_is_rejected():
    installment = Installment(payment_rule=make_rule(is_active=999), deal=make_deal())
    assert InstallmentValidator(None).validate([installment]) == []


def test_installment_with_mid_recovery_state_is_rejected_for_autopayment():
    # autopayment требует именно SCHEDULED (269) — MID_RECOVERY (271) не годится,
    # это единственный вход только для recovery.
    installment = Installment(payment_rule=make_rule(is_active=PaymentRuleState.MID_RECOVERY), deal=make_deal())
    assert InstallmentValidator(None).validate([installment]) == []


def test_installment_without_driver_id_is_rejected():
    installment = Installment(payment_rule=make_rule(driver_id=None), deal=make_deal())
    assert InstallmentValidator(None).validate([installment]) == []


def test_installment_fully_paid_deal_is_rejected():
    installment = Installment(payment_rule=make_rule(), deal=make_deal(installment_pay_sum=10000))
    assert InstallmentValidator(None).validate([installment]) == []


def test_installment_without_deal_is_rejected():
    installment = Installment(payment_rule=make_rule(), deal=None)
    assert InstallmentValidator(None).validate([installment]) == []
