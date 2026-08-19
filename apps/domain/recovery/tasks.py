from apps.core.tasks import automation_task
from apps.domain.recovery.application.recovery import RecoveryApplication


@automation_task(module_key="recovery")
def run_recovery():
    RecoveryApplication().execute()
