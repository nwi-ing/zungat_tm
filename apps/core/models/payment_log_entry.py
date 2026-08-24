from django.db import models

from apps.core.models.log_entry import LogEntry


class PaymentLogEntry(models.Model):
    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE, related_name="payments")
    driver_id = models.IntegerField(null=True, blank=True)
    deal_id = models.IntegerField(null=True, blank=True)
    fact_payment_id = models.IntegerField(null=True, blank=True)
    amount = models.FloatField(null=True, blank=True)
    arrest_amount = models.FloatField(null=True, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        db_table = "core_payment_log_entry"
        indexes = [
            models.Index(fields=["driver_id"]),
            models.Index(fields=["deal_id"]),
        ]
        verbose_name = "Платёж в логе"
        verbose_name_plural = "Платежи в логах"

    def __str__(self):
        return f"driver={self.driver_id} deal={self.deal_id} amount={self.amount}"
