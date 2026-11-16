from ..models import Recommendation
from .base import ProductContext, Rule, RuleResult, money, register

Severity = Recommendation.Severity


@register
class RatingDropRule(Rule):
    """Star rating is the biggest driver of conversion; catch declines early."""

    code = "rating_drop"
    category = Recommendation.Category.LISTING
    DROP_THRESHOLD = 0.2
    FLOOR = 4.0
    REVENUE_LOSS_PER_STAR = 0.25  # heuristic: one full star ≈ 25% fewer sales

    def evaluate(self, ctx: ProductContext):
        if ctx.rating_30d_ago is None:
            return None
        now, before = float(ctx.rating), float(ctx.rating_30d_ago)
        drop = before - now
        if drop < self.DROP_THRESHOLD and now >= self.FLOOR:
            return None

        severity = Severity.HIGH if now < 3.8 or drop >= 0.4 else Severity.MEDIUM
        stars_at_risk = max(drop, self.FLOOR - now, 0.1)
        impact = float(ctx.revenue_30d) * self.REVENUE_LOSS_PER_STAR * stars_at_risk
        return RuleResult(
            severity=severity,
            title=f"Investigate falling rating on {ctx.title}",
            message=(
                f"Rating went from {before:.1f}★ to {now:.1f}★ in 30 days. Check recent 1–2★ reviews for a "
                f"recurring defect, fix the product or listing, and use Request a Review on happy orders."
            ),
            estimated_impact=money(impact),
            evidence={"rating": now, "rating_30d_ago": before, "drop": round(drop, 2)},
        )


@register
class LowConversionRule(Rule):
    """Plenty of traffic but few purchases usually means the listing itself is the problem."""

    code = "low_conversion"
    category = Recommendation.Category.LISTING
    MIN_SESSIONS = 300  # need enough traffic for the rate to mean something
    THRESHOLD = 0.06
    BENCHMARK = 0.10  # typical unit session percentage for the category

    def evaluate(self, ctx: ProductContext):
        if ctx.sessions_30d < self.MIN_SESSIONS:
            return None
        rate = ctx.conversion_rate
        if rate >= self.THRESHOLD:
            return None

        severity = Severity.HIGH if rate < 0.03 else Severity.MEDIUM if rate < 0.045 else Severity.LOW
        # Assume fixing the listing closes half the gap to the benchmark.
        extra_units = (self.BENCHMARK - rate) * 0.5 * ctx.sessions_30d
        return RuleResult(
            severity=severity,
            title=f"Improve the listing for {ctx.title}",
            message=(
                f"{ctx.sessions_30d:,} visits but only {rate:.1%} converted (category benchmark ≈ "
                f"{self.BENCHMARK:.0%}). Refresh the main image, tighten the title and bullets, and add A+ content."
            ),
            estimated_impact=money(extra_units * float(ctx.price)),
            evidence={"sessions_30d": ctx.sessions_30d, "units_30d": ctx.units_30d, "conversion_pct": round(rate * 100, 2)},
        )
