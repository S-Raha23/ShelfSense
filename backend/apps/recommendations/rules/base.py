"""
Rule framework (Strategy pattern + registry).

A rule is a small class with an `evaluate(ctx)` method. It receives a `ProductContext` — plain,
precomputed numbers — and returns a `RuleResult` or None. Rules never touch the database, which
keeps them pure functions: trivially unit-testable and cheap to run for thousands of products.

Adding a rule = write a class, decorate it with @register. The engine picks it up automatically.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class ProductContext:
    product_id: int
    asin: str
    title: str
    price: Decimal
    competitor_price: Decimal | None
    rating: Decimal
    rating_30d_ago: Decimal | None
    inventory_qty: int
    units_7d: int
    units_30d: int
    revenue_30d: Decimal
    sessions_30d: int

    @property
    def avg_daily_units(self) -> float:
        """Recent sales velocity (last 7 days) — reacts faster than a 30-day average."""
        return self.units_7d / 7

    @property
    def days_of_cover(self) -> float:
        velocity = self.avg_daily_units
        return float("inf") if velocity == 0 else self.inventory_qty / velocity

    @property
    def conversion_rate(self) -> float:
        return self.units_30d / self.sessions_30d if self.sessions_30d else 0.0


@dataclass(frozen=True)
class RuleResult:
    severity: int  # Recommendation.Severity value
    title: str
    message: str
    estimated_impact: Decimal
    evidence: dict = field(default_factory=dict)


class Rule(ABC):
    code: str
    category: str

    @abstractmethod
    def evaluate(self, ctx: ProductContext) -> RuleResult | None: ...


RULES: dict[str, type[Rule]] = {}


def register(rule_cls: type[Rule]) -> type[Rule]:
    if rule_cls.code in RULES:
        raise ValueError(f"Duplicate rule code: {rule_cls.code}")
    RULES[rule_cls.code] = rule_cls
    return rule_cls


def money(value) -> Decimal:
    return Decimal(str(round(float(value), 2)))
