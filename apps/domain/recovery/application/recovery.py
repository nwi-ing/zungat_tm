from apps.integrations.bx24.lib.services.client import Bx24Client
from apps.integrations.tm_driver.lib.services.client import TaxiMasterClient as TMClient

from apps.domain.recovery.services import (
    DriverLoader, DriverValidator, DriverAllocation, CreatePayment
)


class RecoveryApplication:

    def __init__(self, bx_client: Bx24Client = None, tm_client: TMClient = None):
        self.bx_client = bx_client or Bx24Client()
        self.tm_client = tm_client or TMClient()

    def execute(self):
        drivers = DriverLoader(self.bx_client).load()
        drivers = DriverValidator().validate(drivers)
        drivers = DriverAllocation(self.tm_client).allocate(drivers)
        return CreatePayment(self.bx_client).create(drivers)
