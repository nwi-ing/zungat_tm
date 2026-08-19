from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.core.models import AutomationSetting


@staff_member_required
def settings_panel(request):
    return render(request, "core/settings_list.html", {
        "settings": AutomationSetting.objects.order_by("module_key"),
    })


@staff_member_required
@require_POST
def toggle_setting(request, module_key):
    setting = get_object_or_404(AutomationSetting, module_key=module_key)
    setting.enabled = not setting.enabled
    setting.updated_by = request.user
    setting.save(update_fields=["enabled", "updated_by", "updated_at"])
    return render(request, "core/partials/setting_row.html", {"setting": setting})
