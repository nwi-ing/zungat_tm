from django.db import models


class LogEntry(models.Model):
    class Level(models.TextChoices):
        DEBUG = "DEBUG", "Debug"
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        ERROR = "ERROR", "Error"

    created_at = models.DateTimeField(auto_now_add=True)
    module = models.CharField(max_length=50)
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.INFO)
    message = models.TextField()
    context = models.JSONField(default=dict, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "core_log_entry"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["module", "created_at"]),
            models.Index(fields=["level", "created_at"]),
        ]
        verbose_name = "Запись лога"
        verbose_name_plural = "Логи"

    def __str__(self):
        return f"[{self.level}] {self.module}: {self.message[:60]}"
