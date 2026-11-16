from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.accounts.models import Brand


class SyncJob(models.Model):
    """Audit log of every marketplace sync: what ran, when, how much changed, and why it failed."""

    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="sync_jobs")
    triggered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.CharField(max_length=32, default="mock")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RUNNING)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    products_upserted = models.PositiveIntegerField(default=0)
    metrics_upserted = models.PositiveIntegerField(default=0)
    recommendations_created = models.PositiveIntegerField(default=0)
    recommendations_updated = models.PositiveIntegerField(default=0)
    recommendations_expired = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["brand", "-started_at"], name="idx_syncjob_brand_started")]

    def __str__(self):
        return f"{self.brand} sync {self.started_at:%Y-%m-%d %H:%M} ({self.status})"

    @property
    def duration_ms(self):
        if not self.finished_at:
            return None
        return int((self.finished_at - self.started_at).total_seconds() * 1000)
