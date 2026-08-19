import pytest

from apps.domain.recovery.models import DriverSyncState
from apps.domain.recovery.schemas.driver import Driver, Installment
from apps.domain.recovery.services import DriverValidator
from apps.domain.recovery.services.allocator import (
    DriverAllocation, InstallmentAllocation, OperationAllocation,
)
from apps.integrations.bx24.lib.schemas import Deal, PaymentRule, PaymentRuleState
from apps.integrations.tm_driver.lib.schemas import Operation

pytestmark = pytest.mark.django_db


def make_installment(deal_id, total_arest_sum, is_active=PaymentRuleState.SCHEDULED, arested_date=None):
    return Installment(
        deal=Deal(id=deal_id, total_arest_sum=total_arest_sum),
        payment_rule=PaymentRule(id=deal_id, deal_id=deal_id, is_active=is_active, arested_date=arested_date),
    )


def test_driver_validator_drops_disabled_and_zero_arrest_installments():
    driver = Driver(driver_id=1, installments=[
        make_installment(1, total_arest_sum=1000, is_active=PaymentRuleState.SCHEDULED),
        make_installment(2, total_arest_sum=0, is_active=PaymentRuleState.SCHEDULED),
        make_installment(3, total_arest_sum=500, is_active=999),
    ])

    drivers = DriverValidator().validate([driver])

    assert len(drivers) == 1
    assert [i.deal.id for i in drivers[0].installments] == [1]


def test_driver_validator_drops_driver_with_no_valid_installments():
    driver = Driver(driver_id=1, installments=[make_installment(1, total_arest_sum=0)])
    assert DriverValidator().validate([driver]) == []


def test_operation_allocation_filters_only_valid_receipts(fake_tm_client):
    driver = Driver(driver_id=10606, installments=[make_installment(1, 1000)])
    fake_tm_client.operation.seed(Operation(driver_id=10606, sum=500, oper_type="receipt", title="Пополнение", cancelled_oper_id=0, cancelled_by_oper_id=0))
    fake_tm_client.operation.seed(Operation(driver_id=10606, sum=300, oper_type="expense", title="Списание"))
    fake_tm_client.operation.seed(
        Operation(driver_id=10606, sum=200, oper_type="receipt", title="Пополнение", cancelled_oper_id=999)
    )
    fake_tm_client.operation.seed(
        Operation(driver_id=10606, sum=100, oper_type="receipt", title="Отмена пополнения")
    )

    operations = OperationAllocation(fake_tm_client).loadReceiptes(driver)

    assert len(operations) == 1
    assert operations[0].sum == 500


def test_operation_allocation_excludes_already_processed(fake_tm_client):
    driver = Driver(driver_id=10606, installments=[make_installment(1, 1000)])
    op = fake_tm_client.operation.seed(Operation(driver_id=10606, sum=500, oper_type="receipt", title="Пополнение", cancelled_oper_id=0, cancelled_by_oper_id=0))
    DriverSyncState.objects.create(driver_id=10606, last_processed_operation_id=op.id)

    operations = OperationAllocation(fake_tm_client).loadReceiptes(driver)

    assert operations == []


def test_installment_allocation_splits_greedily_across_installments():
    driver = Driver(driver_id=10606, operations=[
        Operation(id=1, driver_id=10606, sum=700, oper_type="receipt"),
    ], installments=[
        make_installment(1, total_arest_sum=400),
        make_installment(2, total_arest_sum=500),
    ])

    installments = InstallmentAllocation().allocate(driver)

    assert installments[0].fact_payment.opportunity == 400
    assert installments[1].fact_payment.opportunity == 300


def test_driver_allocation_end_to_end(fake_tm_client):
    driver = Driver(driver_id=10606, installments=[make_installment(1, total_arest_sum=400)])
    fake_tm_client.operation.seed(Operation(driver_id=10606, sum=1000, oper_type="receipt", title="Пополнение", cancelled_oper_id=0, cancelled_by_oper_id=0))

    drivers = DriverAllocation(fake_tm_client).allocate([driver])

    installment = drivers[0].installments[0]
    assert installment.fact_payment.opportunity == 400
    assert installment.fact_payment.arest_sum is None
