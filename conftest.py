import pytest

from apps.integrations.bx24.testing import FakeBx24Client
from apps.integrations.tm_driver.testing import FakeTaxiMasterClient


@pytest.fixture
def fake_bx_client():
    return FakeBx24Client()


@pytest.fixture
def fake_tm_client():
    return FakeTaxiMasterClient()
