
from apps.integrations.tm_driver.lib.services.client import TaxiMasterClient as TMClient

class CalculateError(Exception):
    pass

class PaymentCalculation:
    def __init__(self,tm_client:TMClient):
        self.tm_client = tm_client
    

    def calculate(self,fact_payment,payment_rule):
        # Отмена платежа не проверяет баланс водителя и не считает
        # перерасход — в отличие от writeoff, отмена должна проходить
        # всегда, независимо от текущего баланса.
        payment_sum = [i for i in [fact_payment.opportunity,fact_payment.arest_sum] if i is not None]

        payment_sum = sum(payment_sum)
        return payment_sum