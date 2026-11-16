"""
Multi-tenancy helpers.

Tenant isolation is enforced in exactly one place: `BrandScopedMixin.get_queryset()`.
Views never filter by brand themselves, so a forgotten filter can't leak another
brand's data — a view that doesn't use the mixin simply has no brand to work with.
"""
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


def get_user_brand(user):
    profile = getattr(user, "profile", None)
    if profile is None:
        raise PermissionDenied("This account is not attached to a brand.")
    return profile.brand


class HasBrand(BasePermission):
    message = "This account is not attached to a brand."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, "profile"))


class BrandScopedMixin:
    """Restricts a view's queryset to the requesting user's brand.

    `brand_lookup` is the ORM path from the model to Brand (e.g. "product__brand").
    """

    brand_lookup = "brand"

    @property
    def brand(self):
        if not hasattr(self, "_brand"):
            self._brand = get_user_brand(self.request.user)
        return self._brand

    def get_queryset(self):
        return super().get_queryset().filter(**{self.brand_lookup: self.brand})
