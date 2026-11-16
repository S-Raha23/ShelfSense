from rest_framework import serializers

from .models import SyncJob


class SyncJobSerializer(serializers.ModelSerializer):
    triggered_by = serializers.CharField(source="triggered_by.username", default=None, read_only=True)
    duration_ms = serializers.IntegerField(read_only=True)

    class Meta:
        model = SyncJob
        fields = [
            "id", "source", "status", "started_at", "finished_at", "duration_ms", "triggered_by",
            "products_upserted", "metrics_upserted", "recommendations_created",
            "recommendations_updated", "recommendations_expired", "error",
        ]
        read_only_fields = fields
