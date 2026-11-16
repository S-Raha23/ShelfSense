"""
Read-side queries for the catalog and dashboard.

Convention used across the project:
  * selectors.py  -> read queries (no side effects)
  * services/     -> write operations / business processes
Views stay thin: they parse the request, call a selector or service, and serialise.

All aggregation happens in PostgreSQL (SUM / GROUP BY via the ORM), never in Python loops.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import DecimalField, F, IntegerField, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce, TruncWeek
from django.utils import timezone

from .models import DailyMetric, Product

ZERO_DEC = Value(Decimal("0"), output_field=DecimalField(max_digits=14, decimal_places=2))
ZERO_INT = Value(0, output_field=IntegerField())


@dataclass(frozen=True)
class Period:
    start: date
    end: date

    @classmethod
    def last_n_days(cls, days: int, today: date | None = None) -> "Period":
        today = today or timezone.localdate()
        return cls(start=today - timedelta(days=days - 1), end=today)

    def previous(self) -> "Period":
        length = (self.end - self.start).days + 1
        return Period(start=self.start - timedelta(days=length), end=self.start - timedelta(days=1))


def _pct_change(current, previous):
    if not previous:
        return None
    return round(float((current - previous) / previous) * 100, 1)


def _safe_div(a, b):
    return float(a) / float(b) if b else 0.0


def products_with_period_stats(brand, period: Period) -> QuerySet:
    return annotate_period_stats(Product.objects.filter(brand=brand), period)


def annotate_period_stats(products: QuerySet, period: Period) -> QuerySet:
    """Annotate products with units / revenue / sessions for the period (a single GROUP BY query)."""
    in_period = Q(daily_metrics__date__range=(period.start, period.end))
    return products.annotate(
        units_period=Coalesce(Sum("daily_metrics__units", filter=in_period), ZERO_INT),
        revenue_period=Coalesce(Sum("daily_metrics__revenue", filter=in_period), ZERO_DEC),
        sessions_period=Coalesce(Sum("daily_metrics__sessions", filter=in_period), ZERO_INT),
    )


def dashboard_summary(brand, period: Period) -> dict:
    """KPIs for the period plus % change vs the previous period of equal length."""
    prev = period.previous()
    cur_q = Q(date__range=(period.start, period.end))
    prev_q = Q(date__range=(prev.start, prev.end))

    # One query computes both periods using conditional aggregation (SUM ... FILTER (WHERE ...)).
    # Result keys are prefixed so they don't shadow the model fields they aggregate.
    agg = DailyMetric.objects.filter(product__brand=brand, date__range=(prev.start, period.end)).aggregate(
        cur_revenue=Coalesce(Sum("revenue", filter=cur_q), ZERO_DEC),
        cur_units=Coalesce(Sum("units", filter=cur_q), ZERO_INT),
        cur_sessions=Coalesce(Sum("sessions", filter=cur_q), ZERO_INT),
        prev_revenue=Coalesce(Sum("revenue", filter=prev_q), ZERO_DEC),
        prev_units=Coalesce(Sum("units", filter=prev_q), ZERO_INT),
        prev_sessions=Coalesce(Sum("sessions", filter=prev_q), ZERO_INT),
    )

    conversion = _safe_div(agg["cur_units"], agg["cur_sessions"])
    prev_conversion = _safe_div(agg["prev_units"], agg["prev_sessions"])
    return {
        "period": {"start": period.start, "end": period.end},
        "revenue": agg["cur_revenue"],
        "units": agg["cur_units"],
        "sessions": agg["cur_sessions"],
        "conversion_rate": round(conversion * 100, 2),
        "avg_selling_price": round(_safe_div(agg["cur_revenue"], agg["cur_units"]), 2),
        "change": {
            "revenue": _pct_change(agg["cur_revenue"], agg["prev_revenue"]),
            "units": _pct_change(agg["cur_units"], agg["prev_units"]),
            "sessions": _pct_change(agg["cur_sessions"], agg["prev_sessions"]),
            "conversion_rate": _pct_change(conversion, prev_conversion),
        },
        "active_products": Product.objects.filter(brand=brand, is_active=True).count(),
    }


def sales_timeseries(brand, period: Period, granularity: str = "day", product=None) -> list[dict]:
    """Revenue / units / sessions grouped by day or ISO week."""
    qs = DailyMetric.objects.filter(product__brand=brand, date__range=(period.start, period.end))
    if product is not None:
        qs = qs.filter(product=product)
    bucket = TruncWeek("date") if granularity == "week" else F("date")
    rows = (
        qs.annotate(bucket=bucket)
        .values("bucket")
        .annotate(revenue=Sum("revenue"), units=Sum("units"), sessions=Sum("sessions"))
        .order_by("bucket")
    )
    return [
        {"date": r["bucket"], "revenue": r["revenue"], "units": r["units"], "sessions": r["sessions"]}
        for r in rows
    ]


def top_products(brand, period: Period, limit: int = 5) -> QuerySet:
    return products_with_period_stats(brand, period).order_by("-revenue_period")[:limit]
