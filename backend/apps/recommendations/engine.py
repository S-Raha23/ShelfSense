"""
Recommendation engine: build one ProductContext per product (a single SQL query), run every
registered rule against it, and reconcile the results with what's already stored.

Lifecycle of a recommendation
  * Rule fires, nothing open        -> create (status OPEN)
  * Rule fires, already open        -> update numbers in place (no duplicates)
  * Rule stops firing while open    -> EXPIRED (the problem went away)
  * User marks DONE / DISMISSED     -> the same rule is snoozed for that product for
                                       COOLDOWN, so we respect the user's decision
"""
from dataclasses import dataclass
from datetime import timedelta

from django.db.models import DecimalField, IntegerField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.catalog.models import DailyMetric, Product

from .models import Recommendation
from .rules import RULES, ProductContext

COOLDOWN = timedelta(days=14)


@dataclass
class EngineResult:
    created: int = 0
    updated: int = 0
    expired: int = 0


def build_contexts(brand, today=None) -> list[ProductContext]:
    today = today or timezone.localdate()
    d7, d30 = today - timedelta(days=6), today - timedelta(days=29)
    last_7 = Q(daily_metrics__date__range=(d7, today))
    last_30 = Q(daily_metrics__date__range=(d30, today))
    rating_30d_ago = (
        DailyMetric.objects.filter(product=OuterRef("pk"), date__lte=d30).order_by("-date").values("rating")[:1]
    )
    zero_int = Value(0, output_field=IntegerField())
    products = Product.objects.filter(brand=brand, is_active=True).annotate(
        units_7d=Coalesce(Sum("daily_metrics__units", filter=last_7), zero_int),
        units_30d=Coalesce(Sum("daily_metrics__units", filter=last_30), zero_int),
        sessions_30d=Coalesce(Sum("daily_metrics__sessions", filter=last_30), zero_int),
        revenue_30d=Coalesce(
            Sum("daily_metrics__revenue", filter=last_30), Value(0, output_field=DecimalField())
        ),
        rating_30d_ago=Subquery(rating_30d_ago, output_field=DecimalField()),
    )
    return [
        ProductContext(
            product_id=p.pk,
            asin=p.asin,
            title=p.title,
            price=p.price,
            competitor_price=p.competitor_price,
            rating=p.rating,
            rating_30d_ago=p.rating_30d_ago,
            inventory_qty=p.inventory_qty,
            units_7d=p.units_7d,
            units_30d=p.units_30d,
            revenue_30d=p.revenue_30d,
            sessions_30d=p.sessions_30d,
        )
        for p in products
    ]


def generate_recommendations(brand, today=None) -> EngineResult:
    now = timezone.now()
    result = EngineResult()
    rules = [rule_cls() for rule_cls in RULES.values()]

    open_recs = {
        (r.product_id, r.rule_code): r
        for r in Recommendation.objects.filter(brand=brand, status=Recommendation.Status.OPEN)
    }
    snoozed = set(
        Recommendation.objects.filter(
            brand=brand,
            status__in=[Recommendation.Status.DONE, Recommendation.Status.DISMISSED],
            resolved_at__gte=now - COOLDOWN,
        ).values_list("product_id", "rule_code")
    )

    to_create, to_update, still_firing = [], [], set()
    for ctx in build_contexts(brand, today):
        for rule in rules:
            outcome = rule.evaluate(ctx)
            key = (ctx.product_id, rule.code)
            if outcome is None or key in snoozed:
                continue
            still_firing.add(key)
            fields = dict(
                category=rule.category,
                severity=outcome.severity,
                title=outcome.title,
                message=outcome.message,
                estimated_impact=outcome.estimated_impact,
                evidence=outcome.evidence,
            )
            if key in open_recs:
                rec = open_recs[key]
                for name, value in fields.items():
                    setattr(rec, name, value)
                rec.updated_at = now
                to_update.append(rec)
            else:
                to_create.append(Recommendation(brand=brand, product_id=ctx.product_id, rule_code=rule.code, **fields))

    Recommendation.objects.bulk_create(to_create)
    Recommendation.objects.bulk_update(
        to_update, ["category", "severity", "title", "message", "estimated_impact", "evidence", "updated_at"]
    )
    stale_ids = [rec.pk for key, rec in open_recs.items() if key not in still_firing]
    result.expired = Recommendation.objects.filter(pk__in=stale_ids).update(
        status=Recommendation.Status.EXPIRED, resolved_at=now
    )
    result.created, result.updated = len(to_create), len(to_update)
    return result
