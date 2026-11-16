from ..models import Recommendation
from .base import ProductContext, Rule, RuleResult, money, register

Severity = Recommendation.Severity


@register
class PriceGapRule(Rule):
    """Priced well above comparable offers: on Amazon this costs Buy Box share and conversion."""

    code = "price_gap"
    category = Recommendation.Category.PRICING
    MAX_PREMIUM = 0.10  # tolerate up to 10% above competition (brand premium)
    TARGET_PREMIUM = 0.03  # suggested price: competitor + 3%
    ELASTICITY = 2.0  # assumed price elasticity of demand: 1% cheaper -> ~2% more units

    def evaluate(self, ctx: ProductContext):
        if not ctx.competitor_price:
            return None
        price, competitor = float(ctx.price), float(ctx.competitor_price)
        gap = (price - competitor) / competitor
        if gap <= self.MAX_PREMIUM:
            return None

        suggested = round(competitor * (1 + self.TARGET_PREMIUM), 2)
        price_drop = (price - suggested) / price
        projected_units = ctx.units_30d * (1 + self.ELASTICITY * price_drop)
        revenue_change = suggested * projected_units - price * ctx.units_30d
        severity = Severity.HIGH if gap > 0.25 else Severity.MEDIUM if gap > 0.15 else Severity.LOW
        return RuleResult(
            severity=severity,
            title=f"Reprice {ctx.title}",
            message=(
                f"Your price ${price:.2f} is {gap:.0%} above the competing offer at ${competitor:.2f}. "
                f"Repricing to ${suggested:.2f} could lift units by ~{self.ELASTICITY * price_drop:.0%} "
                f"and improve Buy Box share."
            ),
            estimated_impact=money(revenue_change),
            evidence={
                "price": price,
                "competitor_price": competitor,
                "gap_pct": round(gap * 100, 1),
                "suggested_price": suggested,
            },
        )
