import pytest

from apps.domain.autopayment.schemas.installment import Installment
from apps.domain.autopayment.services import InstallmentCalculation
from apps.integrations.bx24.lib.schemas import Deal, PaymentRule
from apps.integrations.tm_driver.lib.schemas import Driver

pytestmark = pytest.mark.django_db


def make_installment(payment_sum, opportunity, total_arest_sum=0, installment_pay_sum=0):
    return Installment(
        payment_rule=PaymentRule(id=1, deal_id=1, driver_id=10606, payment_sum=payment_sum),
        deal=Deal(id=1, opportunity=opportunity, total_arest_sum=total_arest_sum, installment_pay_sum=installment_pay_sum),
    )


def test_payment_sum_capped_by_remaining_installment_amount(fake_tm_client):
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=10000))
    installment = make_installment(payment_sum=1000, opportunity=1500, installment_pay_sum=1000)

    result = InstallmentCalculation(fake_tm_client).calculate([installment])

    # осталось только 500 до полного закрытия, хотя плановый платёж 1000
    assert result[0].operation.oper_sum == 500


def test_payment_sum_zero_when_already_fully_paid(fake_tm_client):
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=10000))
    installment = make_installment(payment_sum=1000, opportunity=1000, installment_pay_sum=1000)

    result = InstallmentCalculation(fake_tm_client).calculate([installment])

    assert result[0].operation.oper_sum == 0


def test_fact_payment_split_when_balance_insufficient(fake_tm_client):
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=300))
    installment = make_installment(payment_sum=1000, opportunity=5000)

    result = InstallmentCalculation(fake_tm_client).calculate([installment])

    assert result[0].fact_payment.opportunity == 300
    assert result[0].fact_payment.arest_sum == 700


def test_fact_payment_fully_paid_when_balance_sufficient(fake_tm_client):
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=10000))
    installment = make_installment(payment_sum=1000, opportunity=5000)

    result = InstallmentCalculation(fake_tm_client).calculate([installment])

    assert result[0].fact_payment.opportunity == 1000
    assert result[0].fact_payment.arest_sum == 0


def test_two_installments_same_driver_do_not_double_count_balance(fake_tm_client):
    # Один и тот же водитель, две рассрочки списываются в одном запуске.
    # Баланс должен "расходоваться" последовательно, а не читаться заново
    # с нуля для каждой рассрочки (баг: обе считали одну и ту же сумму
    # как покрытую балансом).
    fake_tm_client.driver.seed(Driver(driver_id=10606, balance=73.57))
    first = make_installment(payment_sum=3750, opportunity=20000)
    second = make_installment(payment_sum=6800, opportunity=20000)

    result = InstallmentCalculation(fake_tm_client).calculate([first, second])

    assert result[0].fact_payment.opportunity == 73.57
    assert result[0].fact_payment.arest_sum == 3676.43

    assert result[1].fact_payment.opportunity == 0
    assert result[1].fact_payment.arest_sum == 6800
