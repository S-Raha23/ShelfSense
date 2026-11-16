from django.conf import settings
from django.db import models


class Brand(models.Model):
    """A tenant. Every product, metric, recommendation and sync job belongs to one brand."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Profile(models.Model):
    """Links a Django user to the brand they work for."""

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ANALYST = "analyst", "Analyst"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="members")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.OWNER)

    def __str__(self):
        return f"{self.user} @ {self.brand}"
