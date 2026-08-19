from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render

from apps.core.models import LogEntry

PAGE_SIZE = 50


def _filtered_queryset(request):
    qs = LogEntry.objects.all()
    module = request.GET.get("module") or ""
    level = request.GET.get("level") or ""
    if module:
        qs = qs.filter(module=module)
    if level:
        qs = qs.filter(level=level)
    return qs, module, level


@staff_member_required
def log_list(request):
    qs, module, level = _filtered_queryset(request)
    paginator = Paginator(qs, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page") or 1)

    context = {
        "page": page,
        "modules": LogEntry.objects.order_by().values_list("module", flat=True).distinct(),
        "levels": LogEntry.Level.choices,
        "selected_module": module,
        "selected_level": level,
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "core/partials/logs_table.html", context)
    return render(request, "core/logs_list.html", context)
