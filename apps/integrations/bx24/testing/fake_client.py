from itertools import count

from apps.integrations.bx24.lib.schemas import (
    Company,
    Contact,
    Deal,
    FactPayment,
    Lead,
    PaymentRule,
    PlanPayment,
)

_FILTER_OPERATORS = ("!@", ">=", "<=", "=%", ">", "<", "!", "%", "@")


class FakeCRMTimelineClient:
    """Records timeline messages instead of calling Bitrix, so tests can
    assert on _addError/_addEvent-style calls without a real request."""

    def __init__(self):
        self.messages = []

    def add(self, timeline_message):
        self.messages.append(timeline_message)
        return timeline_message

    def list(self):
        return []

    def delete(self, id):
        self.messages = [m for m in self.messages if m.message_id != id]
        return None


def _matches(entity, filters):
    for key, value in (filters or {}).items():
        op = ""
        field_name = key
        for candidate in _FILTER_OPERATORS:
            if key.startswith(candidate):
                op, field_name = candidate, key[len(candidate):]
                break

        actual = getattr(entity, field_name, None)

        if op == "!@":
            if actual in value:
                return False
        elif op == "!":
            if actual == value:
                return False
        elif isinstance(value, (list, tuple, set)):
            if actual not in value:
                return False
        elif actual != value:
            return False
    return True


class FakeCRMEntityClient:
    """In-memory stand-in for BaseCRMClient (apps/integrations/bx24/lib/services/crm/crm_client.py).
    Duck-types get/list/iter_list/add/update/delete/fields — no Protocol needed,
    nothing in the real codebase types against an interface either."""

    def __init__(self, pydantic_class, entities=None):
        self.pydantic_class = pydantic_class
        self.timeline = FakeCRMTimelineClient()
        self._store = {}
        self._id_seq = count(1)
        for entity in entities or []:
            self.seed(entity)

    def seed(self, entity):
        if entity.id is None:
            entity = entity.model_copy(update={"id": next(self._id_seq)})
        self._store[entity.id] = entity
        return entity

    def get(self, entity_id):
        return self._store.get(entity_id)

    def list(self, filters: dict = {}):
        return [e for e in self._store.values() if _matches(e, filters)]

    def iter_list(self, filters: dict | None = None, select=None, order=None):
        yield from self.list(filters or {})

    def add(self, obj):
        return self.seed(obj)

    def update(self, obj):
        existing = self._store.get(obj.id)
        if existing is None:
            return None
        merged_data = existing.model_dump()
        merged_data.update(obj.model_dump(exclude_none=True, exclude={"id"}))
        merged = self.pydantic_class(**merged_data)
        self._store[obj.id] = merged
        return merged

    def delete(self, entity_id):
        return self._store.pop(entity_id, None)

    def fields(self):
        return {}


class FakeBx24Client:
    def __init__(self):
        self.deal = FakeCRMEntityClient(Deal)
        self.payment_rule = FakeCRMEntityClient(PaymentRule)
        self.fact_payment = FakeCRMEntityClient(FactPayment)
        self.contact = FakeCRMEntityClient(Contact)
        self.company = FakeCRMEntityClient(Company)
        self.lead = FakeCRMEntityClient(Lead)
        self.plan_payment = FakeCRMEntityClient(PlanPayment)
