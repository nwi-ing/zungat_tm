from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.shortcuts import render, get_object_or_404

from apps.core.models import LogEntry

PAGE_SIZE = 50


def _filtered_queryset(request):
    qs = LogEntry.objects.annotate(
        payments_count=Count("payments"),
        payments_total=Sum("payments__amount"),
    )
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


@staff_member_required
def log_payments(request, log_id):
    entry = get_object_or_404(LogEntry, pk=log_id)
    return render(request, "core/partials/log_payments.html", {"payments": entry.payments.all()})
