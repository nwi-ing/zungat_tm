from django.conf import settings
from django.db import models


class AutomationSetting(models.Model):
    module_key = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=150, blank=True)
    enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        db_table = "core_automation_setting"
        verbose_name = "Настройка автоматизации"
        verbose_name_plural = "Настройки автоматизации"

    def __str__(self):
        return f"{self.label or self.module_key} ({'включено' if self.enabled else 'выключено'})"
