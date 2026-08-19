from itertools import count

from apps.integrations.tm_driver.lib.schemas import Driver, Operation


class FakeDriverClient:
    def __init__(self, drivers=None):
        self._drivers = {d.id: d for d in (drivers or [])}

    def seed(self, driver: Driver):
        self._drivers[driver.id] = driver
        return driver

    def get(self, id):
        return self._drivers[id]

    def add(self, driver: Driver):
        return self.seed(driver)

    def update(self):
        return None

    def delete(self):
        return None

    def list(self, locked_drivers=False, dismissed_drivers=False, fields=""):
        return list(self._drivers.values())


class FakeOperationClient:
    def __init__(self, operations=None):
        self._operations = list(operations or [])
        max_id = max((o.id or 0 for o in self._operations), default=0)
        self._id_seq = count(max_id + 1)

    def seed(self, operation: Operation):
        if operation.id is None:
            operation = operation.model_copy(update={"id": next(self._id_seq)})
        self._operations.append(operation)
        return operation

    def get(self, driver_id, start_time, finish_time):
        return [o for o in self._operations if o.driver_id == driver_id]

    def add(self, operation: Operation):
        return self.seed(operation)

    def cencel(self):
        ...


class FakeTaxiMasterClient:
    def __init__(self, drivers=None, operations=None):
        self.driver = FakeDriverClient(drivers)
        self.operation = FakeOperationClient(operations)
