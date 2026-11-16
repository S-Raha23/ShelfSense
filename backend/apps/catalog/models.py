from django.db import models

from apps.accounts.models import Brand


class Product(models.Model):
    """An Amazon listing (ASIN) owned by a brand.

    Price, rating, reviews and inventory are a *denormalised snapshot* of the latest
    synced values, so list views never need to dig through history. The full history
    lives in `DailyMetric`.
    """

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="products")
    asin = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=120, blank=True)
    image_url = models.URLField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    competitor_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)
    inventory_qty = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        constraints = [
            # Natural key used by the sync's upsert (INSERT ... ON CONFLICT).
            models.UniqueConstraint(fields=["brand", "asin"], name="uniq_product_brand_asin"),
        ]

    def __str__(self):
        return f"{self.asin} · {self.title}"


class DailyMetric(models.Model):
    """One row per product per day: a fact table for sales and traffic.

    Mirrors what Amazon's Sales & Traffic report returns, plus the day's price,
    competitor price, rating and inventory so trends can be analysed over time.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="daily_metrics")
    date = models.DateField()
    units = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sessions = models.PositiveIntegerField(default=0, help_text="Product detail page visits.")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    competitor_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    inventory_qty = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["product", "date"]
        constraints = [
            # Makes re-running a sync idempotent: the same day is updated, never duplicated.
            models.UniqueConstraint(fields=["product", "date"], name="uniq_metric_product_date"),
        ]
        indexes = [
            # Dashboard queries filter a brand's metrics by date range.
            models.Index(fields=["date"], name="idx_metric_date"),
        ]

    def __str__(self):
        return f"{self.product.asin} {self.date}"
