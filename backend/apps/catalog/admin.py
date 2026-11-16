from django.contrib import admin

from .models import DailyMetric, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["asin", "title", "brand", "price", "rating", "inventory_qty", "last_synced_at"]
    list_filter = ["brand", "category", "is_active"]
    search_fields = ["asin", "title"]


@admin.register(DailyMetric)
class DailyMetricAdmin(admin.ModelAdmin):
    list_display = ["product", "date", "units", "revenue", "sessions", "inventory_qty"]
    list_filter = ["product__brand"]
    date_hierarchy = "date"
    list_select_related = ["product"]
