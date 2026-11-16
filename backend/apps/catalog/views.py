from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.tenancy import BrandScopedMixin, HasBrand, get_user_brand
from apps.recommendations.models import Recommendation

from . import selectors
from .models import Product
from .serializers import (
    DailyMetricSerializer,
    PeriodQuerySerializer,
    ProductSerializer,
    SummarySerializer,
    TimeseriesPointSerializer,
)

PERIOD_PARAMS = [
    OpenApiParameter("days", int, description="Length of the period ending today (7-90, default 30)."),
]


def parse_period(request):
    params = PeriodQuerySerializer(data=request.query_params)
    params.is_valid(raise_exception=True)
    return selectors.Period.last_n_days(params.validated_data["days"]), params.validated_data


@extend_schema(parameters=PERIOD_PARAMS)
class ProductViewSet(BrandScopedMixin, viewsets.ReadOnlyModelViewSet):
    """Products are read-only over the API: they are created and updated by the marketplace sync."""

    serializer_class = ProductSerializer
    permission_classes = [HasBrand]
    queryset = Product.objects.all()
    search_fields = ["title", "asin", "category"]
    ordering_fields = ["title", "price", "rating", "inventory_qty", "revenue_period", "units_period"]
    ordering = ["-revenue_period"]
    filterset_fields = ["category", "is_active"]

    def get_queryset(self):
        period, _ = parse_period(self.request)
        # Counted with a correlated subquery, not a second JOIN: joining both daily_metrics and
        # recommendations in one query would multiply rows and inflate the revenue SUM.
        open_recs = (
            Recommendation.objects.filter(product=OuterRef("pk"), status=Recommendation.Status.OPEN)
            .values("product")
            .annotate(c=Count("id"))
            .values("c")
        )
        brand_products = super().get_queryset()  # tenant filter applied by BrandScopedMixin
        return selectors.annotate_period_stats(brand_products, period).annotate(
            open_recommendations=Coalesce(Subquery(open_recs, output_field=IntegerField()), 0)
        )

    @extend_schema(parameters=PERIOD_PARAMS, responses=DailyMetricSerializer(many=True))
    @action(detail=True, methods=["get"])
    def metrics(self, request, pk=None):
        """Daily history for one product (used by the product detail chart)."""
        product = self.get_object()
        period, _ = parse_period(request)
        qs = product.daily_metrics.filter(date__range=(period.start, period.end)).order_by("date")
        return Response(DailyMetricSerializer(qs, many=True).data)


class DashboardSummaryView(APIView):
    permission_classes = [HasBrand]

    @extend_schema(parameters=PERIOD_PARAMS, responses=SummarySerializer)
    def get(self, request):
        period, _ = parse_period(request)
        data = selectors.dashboard_summary(get_user_brand(request.user), period)
        return Response(SummarySerializer(data).data)


class DashboardTimeseriesView(APIView):
    permission_classes = [HasBrand]

    @extend_schema(
        parameters=PERIOD_PARAMS + [OpenApiParameter("granularity", str, enum=["day", "week"])],
        responses=TimeseriesPointSerializer(many=True),
    )
    def get(self, request):
        period, params = parse_period(request)
        rows = selectors.sales_timeseries(get_user_brand(request.user), period, params["granularity"])
        return Response(TimeseriesPointSerializer(rows, many=True).data)


class DashboardTopProductsView(APIView):
    permission_classes = [HasBrand]

    @extend_schema(
        parameters=PERIOD_PARAMS + [OpenApiParameter("limit", int)],
        responses=ProductSerializer(many=True),
    )
    def get(self, request):
        period, params = parse_period(request)
        products = selectors.top_products(get_user_brand(request.user), period, params["limit"])
        return Response(ProductSerializer(products, many=True).data)
