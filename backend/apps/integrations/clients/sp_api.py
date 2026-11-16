"""
Adapter for Amazon's Selling Partner API (SP-API).

Not wired to live credentials in this project (that requires a registered seller/developer
account), but it documents exactly how each `MarketplaceClient` method maps to SP-API so the
real integration is a drop-in replacement for `MockAmazonClient`:

  fetch_catalog
    * Listings Items API  GET /listings/2021-08-01/items/{sellerId}      -> ASIN, title, price
    * Catalog Items API   GET /catalog/2022-04-01/items/{asin}           -> category, images
    * FBA Inventory API   GET /fba/inventory/v1/summaries                -> fulfillable qty
    * Product Pricing API GET /products/pricing/v0/competitivePrice      -> competitor / Buy Box price

  fetch_daily_metrics
    * Reports API: create GET_SALES_AND_TRAFFIC_REPORT (asinGranularity=CHILD,
      dateGranularity=DAY), poll until DONE, download + decompress the JSON document.
      Gives units ordered, ordered product sales and sessions per ASIN per day.

Operational concerns the real adapter must handle:
  * Auth: exchange the long-lived refresh token for a 1-hour LWA access token, cache it.
  * Rate limits: each operation has its own token-bucket quota; 429 -> raise
    TransientMarketplaceError so the shared retry helper backs off exponentially.
  * Reports are asynchronous, so in production this runs in a background worker (Celery),
    not inside an HTTP request.
"""
from django.conf import settings

from .base import MarketplaceClient, MarketplaceError

LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
SP_API_BASE_URL = "https://sellingpartnerapi-na.amazon.com"


class SPAPIClient(MarketplaceClient):
    name = "sp_api"

    def __init__(self):
        self.config = settings.SP_API
        if not self.config["REFRESH_TOKEN"]:
            raise MarketplaceError(
                "SP-API credentials are not configured. Set SP_API_* environment variables "
                "or use MARKETPLACE_CLIENT=mock."
            )

    def fetch_catalog(self, brand):
        raise NotImplementedError("Live SP-API calls are out of scope for this demo; see module docstring.")

    def fetch_daily_metrics(self, brand, asins, start, end):
        raise NotImplementedError("Live SP-API calls are out of scope for this demo; see module docstring.")
