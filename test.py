import os
from datetime import datetime, timezone
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zungat_tm.settings")
django.setup()

from apps.domain.autopayment.application.autopayment2 import (
    AutopaymentApplication
)


def check():
    from apps.integrations.tm_driver.lib.services.client import TaxiMasterClient as TMClient

    drivers = [
        # 4502,
        2859,
        # 9119,
        # 2477,
        # 114,
        # 4480,
        # 10564,
        # 3460,
        # 485,
        # 2666
    ]
    start_time = datetime(year=2026,month=7,day=6,hour=20,minute=6)
    finish_time = datetime.now(timezone.utc)
    for driver in drivers:
        operations = TMClient().operation.get(driver_id=driver,start_time=start_time,finish_time=finish_time)
        operations = [i for i in operations if i.oper_type == "receipt"]
        for i in operations:
            print(i.id,i.create_time,i.sum)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
#                       AUTOPAYMENTS                           #
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
def test_autopayment():
    from datetime import datetime,timezone
    from apps.integrations.bx24.lib.services.client import Bx24Client
    from apps.integrations.tm_driver.lib.services.client import TaxiMasterClient
    from apps.domain.autopayment.services import (
        InstallmentLoader, InstallmentValidator,
        InstallmentCalculation, MakeOperation, CreatePayment
    )

    installments = InstallmentLoader(Bx24Client()).load()
    installments = InstallmentValidator(Bx24Client()).validate(installments)
    print("Корректных платежей:",len(installments))
    installments = InstallmentCalculation(TaxiMasterClient()).calculate(installments)
    # installments = MakeOperation(TaxiMasterClient()).make(installments)
    # installments = CreatePayment(Bx24Client()).create(installments)
    print(
        f"{'Частота':<8}"
        f"{'Rule ID':<10}"
        f"{'Сумма':<15}"
        f"{'Возможность':<15}"
        f"{'Арест':<15}"
        f"{'Начало':<17}"
        f"{'Последний платеж':<17}"
    )

    print("-" * 134)

    for installment in installments:
        first_pay = installment.payment_rule.first_pay_date or ""
        last_pay = installment.payment_rule.last_payment_date or ""


        print(
            f"{str(installment.payment_rule.payment_frequency):<8}"
            f"{installment.payment_rule.id:<10}"
            f"{installment.operation.oper_sum:<15}"
            f"{str(installment.fact_payment.opportunity):<15}"
            f"{installment.fact_payment.arest_sum:<15}"
            f"{first_pay[0:10]:<17}"
            f"{last_pay[0:10]:<17}"
        )
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#



#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
#                       RECOVERY                               #
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

def test_recovery():
    from apps.integrations.bx24.lib.services.client import Bx24Client
    from apps.integrations.tm_driver.lib.services.client import TaxiMasterClient
    from apps.domain.recovery.services import (
        DriverAllocation,DriverLoader,DriverValidator,CreatePayment
    )
    drivers = DriverLoader(Bx24Client()).load()
    print("Список запрошенных водителей:",len(drivers))
    
    
    drivers = DriverValidator().validate(drivers)
    print("Корректных водителей:",len(drivers))
    drivers = DriverAllocation(TaxiMasterClient()).allocate(drivers)

    print(
        f"{'Driver ID':<12}"
        f"{'Deal ID':<10}"
        f"{'Opportunity':<15}"
        f"{'Pay Sum':<15}"
        f"{'Total Arrest':<15}"
        f"{'Payment sum':<15}"
        f"{'First arest date':<10}"
    )

    print("-" * 67)

    for driver in drivers:
        for installment in driver.installments:
            pay_sum = installment.deal.installment_pay_sum or "-"
            total_arest = installment.deal.total_arest_sum or "-"
            if installment.fact_payment is not None:
                if installment.fact_payment.opportunity is not None:
                    opportunity = installment.fact_payment.opportunity
                else:
                    opportunity = ""
            else:
                opportunity = ""
            
            print(
                f"{driver.driver_id:<12}"
                f"{installment.deal.id:<10}"
                f"{str(installment.deal.opportunity):<15}"
                f"{pay_sum:<15}"
                f"{total_arest:<15}"
                f"{opportunity:<15}"
                f"{installment.payment_rule.arested_date}"
            )


    drivers = CreatePayment(Bx24Client()).create(drivers)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
if __name__ == "__main__": 
    # check()
    # test_recovery()
    test_autopayment()

