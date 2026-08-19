from apps.core.models import AutomationSetting


def is_module_enabled(module_key: str) -> bool:
    return AutomationSetting.objects.filter(module_key=module_key, enabled=True).exists()
