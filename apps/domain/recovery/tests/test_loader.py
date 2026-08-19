import pytest

from apps.domain.recovery.services import DriverLoader
from apps.integrations.bx24.lib.schemas import Deal, PaymentRule, PaymentRuleState

pytestmark = pytest.mark.django_db


def test_loads_active_rules_and_groups_by_driver(fake_bx_client):
    fake_bx_client.deal.add(Deal(id=1, title="Рассрочка №1", total_arest_sum=1000))
    fake_bx_client.deal.add(Deal(id=2, title="Рассрочка №2", total_arest_sum=500))
    fake_bx_client.payment_rule.add(
        PaymentRule(id=10, deal_id=1, driver_id=10606, is_active=PaymentRuleState.SCHEDULED)
    )
    fake_bx_client.payment_rule.add(
        PaymentRule(id=11, deal_id=2, driver_id=10606, is_active=PaymentRuleState.MID_RECOVERY)
    )

    drivers = DriverLoader(fake_bx_client).load()

    assert len(drivers) == 1
    driver = drivers[0]
    assert driver.driver_id == 10606
    assert len(driver.installments) == 2
    assert {i.deal.id for i in driver.installments} == {1, 2}


def test_excludes_fully_disabled_rules(fake_bx_client):
    fake_bx_client.deal.add(Deal(id=1, title="Рассрочка №1", total_arest_sum=1000))
    fake_bx_client.payment_rule.add(
        PaymentRule(id=10, deal_id=1, driver_id=10606, is_active=999)
    )

    drivers = DriverLoader(fake_bx_client).load()

    assert drivers == []
