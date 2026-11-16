from django.conf import settings

from .base import MarketplaceClient


def get_marketplace_client() -> MarketplaceClient:
    """Factory: picks the adapter from the MARKETPLACE_CLIENT setting."""
    if settings.MARKETPLACE_CLIENT == "sp_api":
        from .sp_api import SPAPIClient

        return SPAPIClient()
    from .mock import MockAmazonClient

    return MockAmazonClient()
