"""
The contract every marketplace integration implements.

Business logic (the sync service) depends only on `MarketplaceClient` and these plain
dataclasses — never on a vendor SDK or raw JSON. Swapping the mock for Amazon's real
Selling Partner API, or adding another marketplace, means writing one new adapter.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


class MarketplaceError(Exception):
    """Non-retryable error from a marketplace (bad credentials, invalid request...)."""


class TransientMarketplaceError(MarketplaceError):
    """Retryable error: throttling (HTTP 429), timeouts, 5xx responses."""


@dataclass(frozen=True)
class CatalogItem:
    asin: str
    title: str
    category: str
    price: Decimal
    competitor_price: Decimal | None
    rating: Decimal
    review_count: int
    inventory_qty: int
    image_url: str = ""


@dataclass(frozen=True)
class DailyMetricRecord:
    asin: str
    date: date
    units: int
    revenue: Decimal
    sessions: int
    price: Decimal
    competitor_price: Decimal | None
    rating: Decimal
    inventory_qty: int


class MarketplaceClient(ABC):
    name: str = "base"

    @abstractmethod
    def fetch_catalog(self, brand) -> list[CatalogItem]:
        """Current listings with their latest price, rating, reviews and inventory."""

    @abstractmethod
    def fetch_daily_metrics(self, brand, asins: list[str], start: date, end: date) -> list[DailyMetricRecord]:
        """Per-ASIN, per-day sales and traffic for the inclusive date range."""
