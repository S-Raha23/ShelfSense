from rest_framework import serializers

from .models import DailyMetric, Product


class ProductSerializer(serializers.ModelSerializer):
    # Filled by `products_with_period_stats` annotations.
    units_period = serializers.IntegerField(read_only=True)
    revenue_period = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    sessions_period = serializers.IntegerField(read_only=True)
    conversion_rate = serializers.SerializerMethodField()
    open_recommendations = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "asin", "title", "category", "image_url", "price", "competitor_price",
            "rating", "review_count", "inventory_qty", "is_active", "last_synced_at",
            "units_period", "revenue_period", "sessions_period", "conversion_rate",
            "open_recommendations",
        ]
        read_only_fields = fields

    def get_conversion_rate(self, obj) -> float:
        sessions = getattr(obj, "sessions_period", 0)
        if not sessions:
            return 0.0
        return round(obj.units_period / sessions * 100, 2)


class DailyMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyMetric
        fields = ["date", "units", "revenue", "sessions", "price", "competitor_price", "rating", "inventory_qty"]


class PeriodQuerySerializer(serializers.Serializer):
    """Validates the shared `?days=` and `?granularity=` query params."""

    days = serializers.IntegerField(min_value=7, max_value=90, default=30)
    granularity = serializers.ChoiceField(choices=["day", "week"], default="day")
    limit = serializers.IntegerField(min_value=1, max_value=20, default=5)


class TimeseriesPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    units = serializers.IntegerField()
    sessions = serializers.IntegerField()


class SummarySerializer(serializers.Serializer):
    period = serializers.DictField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    units = serializers.IntegerField()
    sessions = serializers.IntegerField()
    conversion_rate = serializers.FloatField()
    avg_selling_price = serializers.FloatField()
    change = serializers.DictField()
    active_products = serializers.IntegerField()
