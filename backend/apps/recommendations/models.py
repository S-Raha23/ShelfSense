from django.db import models
from django.db.models import Q

from apps.accounts.models import Brand
from apps.catalog.models import Product


class Recommendation(models.Model):
    class Severity(models.IntegerChoices):
        # Stored as integers so "most urgent first" is a plain ORDER BY.
        LOW = 1, "Low"
        MEDIUM = 2, "Medium"
        HIGH = 3, "High"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        DONE = "done", "Done"
        DISMISSED = "dismissed", "Dismissed"
        EXPIRED = "expired", "Expired"  # the condition went away on its own

    class Category(models.TextChoices):
        INVENTORY = "inventory", "Inventory"
        PRICING = "pricing", "Pricing"
        LISTING = "listing", "Listing quality"

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="recommendations")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="recommendations")
    rule_code = models.CharField(max_length=40)
    category = models.CharField(max_length=20, choices=Category.choices)
    severity = models.PositiveSmallIntegerField(choices=Severity.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    estimated_impact = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Estimated monthly revenue at stake (USD) if the recommendation is acted on.",
    )
    evidence = models.JSONField(default=dict, help_text="The numbers that triggered the rule.")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-severity", "-estimated_impact"]
        constraints = [
            # At most one *open* recommendation per product per rule; history can hold many.
            models.UniqueConstraint(
                fields=["product", "rule_code"], condition=Q(status="open"), name="uniq_open_rec_per_product_rule"
            ),
        ]
        indexes = [models.Index(fields=["brand", "status"], name="idx_rec_brand_status")]

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title}"
