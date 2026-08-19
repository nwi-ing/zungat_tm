from apps.core.tasks import automation_task
from apps.domain.autopayment.application.autopayment2 import AutopaymentApplication


@automation_task(module_key="autopayment")
def run_autopayment():
    AutopaymentApplication().execute()
