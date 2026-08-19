from datetime import datetime
import logging

from apps.integrations.bx24.lib.services.client import Bx24Client
from apps.domain.autopayment.schemas.installment import Installment
from apps.integrations.bx24.lib.schemas import FactPayment,PaymentRule

logger = logging.getLogger(__name__)


class CreatePaymentError(Exception):
    pass

class CreatePayment:
    def __init__(self,bx_client:Bx24Client):
        self.bx_client = bx_client



    def _updatePaymentRule(self,installment:Installment):
        installment.fact_payment.tm_payment_id = installment.operation.id
        return installment

    def _createFactPayment(self,installment:Installment):
        try:
            installment.fact_payment = self.bx_client.fact_payment.add(installment.fact_payment)
        except Exception:
            logger.warning(
                "Не удалось создать факт-платёж по рассрочке %s",
                installment.payment_rule.id if installment.payment_rule else None,
                exc_info=True,
            )
            return None
        return installment


    def create(self,installments:list[Installment]):
        created = []
        for installment in installments:
            installment = self._updatePaymentRule(installment)
            installment = self._createFactPayment(installment)
            if installment is None:
                continue
            logger.info("Создание платежа по рассрочке: %s", installment.fact_payment.id)
            created.append(installment)
        return created
