from django.contrib import admin

from apps.domain.recovery.models import DriverSyncState


@admin.register(DriverSyncState)
class DriverSyncStateAdmin(admin.ModelAdmin):
    list_display = ("driver_id", "last_processed_operation_id", "updated_at")
    search_fields = ("driver_id",)
    ordering = ("-updated_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
