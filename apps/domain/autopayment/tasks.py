from apps.core.tasks import automation_task
from apps.domain.autopayment.application.autopayment2 import AutopaymentApplication


@automation_task(module_key="autopayment")
def run_autopayment(ctx):
    installments = AutopaymentApplication().execute()

    payments = []
    for installment in installments:
        fp = installment.fact_payment
        payments.append({
            "driver_id": installment.payment_rule.driver_id if installment.payment_rule else None,
            "deal_id": installment.payment_rule.deal_id if installment.payment_rule else None,
            "fact_payment_id": fp.id if fp else None,
            "amount": fp.opportunity if fp else None,
            "arrest_amount": fp.arest_sum if fp else None,
            "success": True,
        })

    ctx["payments"] = payments
