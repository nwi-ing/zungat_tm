from apps.core.tasks import automation_task
from apps.domain.recovery.application.recovery import RecoveryApplication


@automation_task(module_key="recovery")
def run_recovery(ctx):
    drivers = RecoveryApplication().execute()

    payments = []
    for driver in drivers:
        for installment in driver.installments:
            if installment.fact_payment is None:
                continue
            fp = installment.fact_payment
            payments.append({
                "driver_id": driver.driver_id,
                "deal_id": installment.deal.id if installment.deal else None,
                "fact_payment_id": fp.id,
                "amount": fp.opportunity,
                "success": True,
            })

    ctx["payments"] = payments
    ctx["drivers_processed"] = len(drivers)
