"""Rules are pure functions of a ProductContext, so they're tested without a database."""
from decimal import Decimal

from apps.recommendations.models import Recommendation
from apps.recommendations.rules.inventory import LowStockRule, OverstockRule
from apps.recommendations.rules.listing import LowConversionRule, RatingDropRule
from apps.recommendations.rules.pricing import PriceGapRule
from apps.recommendations.rules.base import ProductContext


def ctx(**overrides):
    base = dict(
        product_id=1, asin="B0TEST0001", title="Test Product", price=Decimal("20.00"),
        competitor_price=Decimal("19.50"), rating=Decimal("4.5"), rating_30d_ago=Decimal("4.5"),
        inventory_qty=1000, units_7d=70, units_30d=300, revenue_30d=Decimal("6000"), sessions_30d=2500,
    )
    base.update(overrides)
    return ProductContext(**base)


def test_healthy_product_triggers_nothing():
    rules = [LowStockRule(), OverstockRule(), PriceGapRule(), RatingDropRule(), LowConversionRule()]
    assert [r.code for r in rules if r.evaluate(ctx())] == []


def test_low_stock_severity_scales_with_days_of_cover():
    # 10 units/day
    assert LowStockRule().evaluate(ctx(inventory_qty=50)).severity == Recommendation.Severity.HIGH  # 5 days
    assert LowStockRule().evaluate(ctx(inventory_qty=100)).severity == Recommendation.Severity.MEDIUM  # 10 days
    assert LowStockRule().evaluate(ctx(inventory_qty=180)).severity == Recommendation.Severity.LOW  # 18 days
    assert LowStockRule().evaluate(ctx(inventory_qty=300)) is None  # 30 days >= lead time


def test_low_stock_reorder_quantity_covers_lead_time_plus_target():
    result = LowStockRule().evaluate(ctx(inventory_qty=50))
    assert result.evidence["reorder_qty"] == 10 * (21 + 30) - 50
    assert result.estimated_impact == Decimal("3200.00")  # (21-5) days * 10 units * $20


def test_low_stock_ignores_products_with_no_sales():
    assert LowStockRule().evaluate(ctx(units_7d=0, inventory_qty=5)) is None


def test_overstock_fires_for_dead_stock():
    result = OverstockRule().evaluate(ctx(units_7d=0, inventory_qty=400))
    assert result is not None
    assert result.evidence["days_of_cover"] is None


def test_price_gap_suggests_competitor_plus_target_premium():
    result = PriceGapRule().evaluate(ctx(price=Decimal("30.00"), competitor_price=Decimal("24.00")))
    assert result.severity == Recommendation.Severity.MEDIUM  # 25% gap
    assert result.evidence["suggested_price"] == 24.72
    assert result.estimated_impact > 0


def test_price_gap_tolerates_small_premium_and_missing_competitor():
    assert PriceGapRule().evaluate(ctx(price=Decimal("21.00"), competitor_price=Decimal("20.00"))) is None
    assert PriceGapRule().evaluate(ctx(competitor_price=None)) is None


def test_rating_drop_and_floor():
    assert RatingDropRule().evaluate(ctx(rating=Decimal("4.1"), rating_30d_ago=Decimal("4.6"))).severity == 3
    assert RatingDropRule().evaluate(ctx(rating=Decimal("3.9"), rating_30d_ago=Decimal("3.9"))) is not None
    assert RatingDropRule().evaluate(ctx(rating=Decimal("4.4"), rating_30d_ago=Decimal("4.5"))) is None
    assert RatingDropRule().evaluate(ctx(rating_30d_ago=None)) is None


def test_low_conversion_needs_enough_traffic():
    assert LowConversionRule().evaluate(ctx(units_30d=100, sessions_30d=4000)) is not None  # 2.5%
    assert LowConversionRule().evaluate(ctx(units_30d=5, sessions_30d=200)) is None  # too little traffic
