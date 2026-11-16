from rest_framework import serializers

from .models import Recommendation


class RecommendationProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    asin = serializers.CharField()
    title = serializers.CharField()


class RecommendationSerializer(serializers.ModelSerializer):
    product = RecommendationProductSerializer(read_only=True)
    severity_label = serializers.CharField(source="get_severity_display", read_only=True)

    class Meta:
        model = Recommendation
        fields = [
            "id", "product", "rule_code", "category", "severity", "severity_label", "title", "message",
            "estimated_impact", "evidence", "status", "created_at", "updated_at", "resolved_at",
        ]
        read_only_fields = fields


class RecommendationSummarySerializer(serializers.Serializer):
    open_total = serializers.IntegerField()
    high = serializers.IntegerField()
    medium = serializers.IntegerField()
    low = serializers.IntegerField()
    total_estimated_impact = serializers.DecimalField(max_digits=14, decimal_places=2)
    by_category = serializers.DictField(child=serializers.IntegerField())
