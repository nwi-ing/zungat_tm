from django.contrib import admin

from apps.core.models import LogEntry, AutomationSetting, PaymentLogEntry


class PaymentLogEntryInline(admin.TabularInline):
    model = PaymentLogEntry
    extra = 0
    fields = ("driver_id", "deal_id", "fact_payment_id", "amount", "arrest_amount", "success", "error_message")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ("created_at", "module", "level", "message", "duration_ms")
    list_filter = ("module", "level")
    search_fields = ("message",)
    readonly_fields = ("created_at", "module", "level", "message", "context", "duration_ms")
    ordering = ("-created_at",)
    inlines = [PaymentLogEntryInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AutomationSetting)
class AutomationSettingAdmin(admin.ModelAdmin):
    list_display = ("module_key", "label", "enabled", "updated_at", "updated_by")
    list_editable = ("enabled",)
    readonly_fields = ("updated_at", "updated_by")

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
