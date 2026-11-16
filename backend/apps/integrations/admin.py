from django.contrib import admin

from .models import SyncJob


@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display = ["brand", "status", "source", "started_at", "products_upserted", "metrics_upserted"]
    list_filter = ["status", "brand", "source"]
    readonly_fields = [f.name for f in SyncJob._meta.fields]
