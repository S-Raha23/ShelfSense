import math

from ..models import Recommendation
from .base import ProductContext, Rule, RuleResult, money, register

Severity = Recommendation.Severity


@register
class LowStockRule(Rule):
    """Warn before a product runs out of stock (a stockout also hurts organic ranking on Amazon)."""

    code = "low_stock"
    category = Recommendation.Category.INVENTORY
    LEAD_TIME_DAYS = 21  # typical time to manufacture/ship and check in to FBA
    TARGET_COVER_DAYS = 30  # stock to hold on top of the lead time

    def evaluate(self, ctx: ProductContext):
        velocity = ctx.avg_daily_units
        cover = ctx.days_of_cover
        if velocity == 0 or cover >= self.LEAD_TIME_DAYS:
            return None

        severity = Severity.HIGH if cover < 7 else Severity.MEDIUM if cover < 14 else Severity.LOW
        reorder_qty = math.ceil(velocity * (self.LEAD_TIME_DAYS + self.TARGET_COVER_DAYS) - ctx.inventory_qty)
        stockout_days = self.LEAD_TIME_DAYS - cover
        revenue_at_risk = stockout_days * velocity * float(ctx.price)
        return RuleResult(
            severity=severity,
            title=f"Restock {ctx.title}",
            message=(
                f"Only {cover:.0f} days of stock left at {velocity:.1f} units/day. Replenishment takes about "
                f"{self.LEAD_TIME_DAYS} days, so reorder ~{reorder_qty:,} units now to avoid a stockout."
            ),
            estimated_impact=money(revenue_at_risk),
            evidence={
                "inventory_qty": ctx.inventory_qty,
                "avg_daily_units": round(velocity, 2),
                "days_of_cover": round(cover, 1),
                "reorder_qty": reorder_qty,
            },
        )


@register
class OverstockRule(Rule):
    """Flag excess inventory that ties up cash and incurs long-term storage fees."""

    code = "overstock"
    category = Recommendation.Category.INVENTORY
    MAX_COVER_DAYS = 120
    HEALTHY_COVER_DAYS = 60
    STORAGE_FEE_PER_UNIT_MONTH = 0.75  # rough blended FBA monthly + aged-inventory fee

    def evaluate(self, ctx: ProductContext):
        if ctx.inventory_qty == 0 or ctx.days_of_cover <= self.MAX_COVER_DAYS:
            return None

        excess_units = ctx.inventory_qty - int(ctx.avg_daily_units * self.HEALTHY_COVER_DAYS)
        monthly_fees = excess_units * self.STORAGE_FEE_PER_UNIT_MONTH
        cover_txt = "no recent sales" if math.isinf(ctx.days_of_cover) else f"{ctx.days_of_cover:.0f} days of cover"
        return RuleResult(
            severity=Severity.MEDIUM if ctx.days_of_cover > 180 else Severity.LOW,
            title=f"Clear excess stock of {ctx.title}",
            message=(
                f"{ctx.inventory_qty} units on hand ({cover_txt}). Around {excess_units} units are surplus. "
                f"Consider a coupon or Lightning Deal to speed up sales, or pause replenishment."
            ),
            estimated_impact=money(monthly_fees),
            evidence={
                "inventory_qty": ctx.inventory_qty,
                "days_of_cover": None if math.isinf(ctx.days_of_cover) else round(ctx.days_of_cover, 1),
                "excess_units": excess_units,
            },
        )
