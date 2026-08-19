import logging

from apps.integrations.tm_driver.lib.services.client import TaxiMasterClient as TMClient
from apps.domain.autopayment.schemas.installment import Installment

logger = logging.getLogger(__name__)


class TMOperationError(Exception):
    pass

class MakeOperation:
    def __init__(self,tm_client:TMClient):
        self.tm_client = tm_client

    
    def make(self,installments:list[Installment]):
        for installment in installments:
            try:
                operation = self.tm_client.operation.add(installment.operation)
                logger.info("Списание по рассрочке: %s", installment.deal.title)
            except:
                continue
            installment.operation = operation
        
        return installments
        