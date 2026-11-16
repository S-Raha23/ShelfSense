from django.contrib import admin

from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ["title", "brand", "rule_code", "severity", "estimated_impact", "status", "updated_at"]
    list_filter = ["status", "severity", "category", "brand"]
    search_fields = ["title", "product__asin"]
    list_select_related = ["product", "brand"]
