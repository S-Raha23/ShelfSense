"""
A realistic stand-in for Amazon's Selling Partner API.

Data is *deterministic*: the same brand + ASIN + date always produces the same numbers,
so repeated syncs are reproducible (and testable) while each new day adds a new data point.
Each product follows a scenario that exercises one recommendation rule, so a fresh
account always has something interesting to look at.
"""
import hashlib
import random
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.utils import timezone

from .base import CatalogItem, DailyMetricRecord, MarketplaceClient, TransientMarketplaceError

# title, category, price, base daily units, scenario
CATALOG = [
    ("Stainless Steel Insulated Water Bottle 32oz", "Kitchen & Dining", 24.99, 38, "healthy"),
    ("Bamboo Cutting Board Set (3 Pack)", "Kitchen & Dining", 29.99, 22, "low_stock"),
    ("Silicone Baking Mat Set", "Kitchen & Dining", 15.99, 30, "healthy"),
    ("Cold Brew Coffee Maker 1.5L", "Kitchen & Dining", 34.99, 14, "overpriced"),
    ("Cast Iron Skillet 12-inch Pre-Seasoned", "Cookware", 39.99, 18, "rating_drop"),
    ("Electric Milk Frother Handheld", "Small Appliances", 19.99, 9, "low_conversion"),
    ("Glass Meal Prep Containers (10 Pack)", "Food Storage", 32.99, 26, "healthy"),
    ("Herb Keeper Fresh Storage Pod", "Food Storage", 21.99, 4, "overstock"),
    ("Digital Kitchen Scale 11lb", "Kitchen Tools", 17.99, 41, "low_stock"),
    ("Pour-Over Coffee Kettle Gooseneck", "Kitchen & Dining", 44.99, 7, "overpriced"),
    ("Reusable Beeswax Food Wraps", "Food Storage", 18.49, 16, "healthy"),
    ("Mandoline Slicer Adjustable", "Kitchen Tools", 27.99, 12, "rating_drop"),
]

# conversion rate, days of inventory cover today, price premium vs competitor, rating today, rating 30d ago
SCENARIOS = {
    "healthy": dict(conversion=0.12, cover_days=48, premium=1.03, rating=4.6, rating_30d=4.6),
    "low_stock": dict(conversion=0.13, cover_days=6, premium=1.02, rating=4.5, rating_30d=4.5),
    "overpriced": dict(conversion=0.08, cover_days=55, premium=1.24, rating=4.4, rating_30d=4.4),
    "rating_drop": dict(conversion=0.10, cover_days=40, premium=1.04, rating=3.8, rating_30d=4.4),
    "low_conversion": dict(conversion=0.035, cover_days=60, premium=1.01, rating=4.3, rating_30d=4.3),
    "overstock": dict(conversion=0.09, cover_days=210, premium=1.05, rating=4.5, rating_30d=4.5),
}

CENT = Decimal("0.01")


def _money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _asin_for(brand_slug: str, index: int) -> str:
    digest = hashlib.sha1(f"{brand_slug}:{index}".encode()).hexdigest()[:8].upper()
    return f"B0{digest}"


class MockAmazonClient(MarketplaceClient):
    name = "mock"

    def __init__(self, failure_rate: float | None = None, today: date | None = None):
        self.failure_rate = settings.MOCK_FAILURE_RATE if failure_rate is None else failure_rate
        self.today = today or timezone.localdate()

    # -- helpers -----------------------------------------------------------
    def _maybe_fail(self):
        """Simulate a flaky third-party API (throttling) so retry logic can be demoed and tested."""
        if self.failure_rate and random.random() < self.failure_rate:
            raise TransientMarketplaceError("429 QuotaExceeded: request was throttled (simulated)")

    def _products(self, brand):
        for i, (title, category, price, units, scenario) in enumerate(CATALOG):
            yield _asin_for(brand.slug, i), title, category, price, units, SCENARIOS[scenario]

    @staticmethod
    def _rating_on(cfg, days_ago: int) -> float:
        # Linear move from the rating 30 days ago to today's rating.
        weight = min(days_ago, 30) / 30
        return cfg["rating"] + (cfg["rating_30d"] - cfg["rating"]) * weight

    @staticmethod
    def _inventory_on(cfg, base_units, days_ago: int) -> int:
        # Stock was higher in the past and has been sold down to today's level.
        return int(base_units * cfg["cover_days"] + base_units * days_ago)

    # -- MarketplaceClient --------------------------------------------------
    def fetch_catalog(self, brand) -> list[CatalogItem]:
        self._maybe_fail()
        items = []
        for asin, title, category, price, units, cfg in self._products(brand):
            items.append(
                CatalogItem(
                    asin=asin,
                    title=title,
                    category=category,
                    price=_money(price),
                    competitor_price=_money(price / cfg["premium"]),
                    rating=_money(self._rating_on(cfg, 0)),
                    review_count=200 + int(hashlib.md5(asin.encode()).hexdigest()[:3], 16),
                    inventory_qty=self._inventory_on(cfg, units, 0),
                )
            )
        return items

    def fetch_daily_metrics(self, brand, asins, start, end) -> list[DailyMetricRecord]:
        self._maybe_fail()
        wanted = set(asins)
        records = []
        for asin, _title, _cat, price, base_units, cfg in self._products(brand):
            if asin not in wanted:
                continue
            day = start
            while day <= end:
                rng = random.Random(f"{asin}:{day.isoformat()}")
                days_ago = (self.today - day).days
                weekend = 1.15 if day.weekday() >= 5 else 1.0
                growth = 1 + 0.004 * (60 - min(days_ago, 60))  # gentle upward trend
                units = max(0, round(base_units * weekend * growth * rng.uniform(0.75, 1.25)))
                sessions = max(units, round(units / cfg["conversion"] * rng.uniform(0.9, 1.1)))
                records.append(
                    DailyMetricRecord(
                        asin=asin,
                        date=day,
                        units=units,
                        revenue=_money(units * price),
                        sessions=sessions,
                        price=_money(price),
                        competitor_price=_money(price / cfg["premium"]),
                        rating=_money(self._rating_on(cfg, days_ago)),
                        inventory_qty=self._inventory_on(cfg, base_units, days_ago),
                    )
                )
                day += timedelta(days=1)
        return records
