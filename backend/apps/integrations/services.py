"""
The marketplace sync: pull catalog + daily metrics from the marketplace adapter, upsert them,
then regenerate recommendations.

Design notes
  * Idempotent: products are upserted on (brand, asin) and metrics on (product, date) using
    PostgreSQL INSERT ... ON CONFLICT DO UPDATE (Django `bulk_create(update_conflicts=True)`).
    Running a sync twice never duplicates data.
  * Network calls happen *outside* the DB transaction (don't hold locks while waiting on a
    third party); all writes happen *inside* one transaction, so a failure leaves the previous
    data intact rather than half-updated.
  * One sync per brand at a time, enforced with a row lock on the brand.
  * Every run is recorded as a SyncJob, including failures and their error message.
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Brand
from apps.catalog.models import DailyMetric, Product
from apps.recommendations.engine import generate_recommendations

from .clients import get_marketplace_client
from .clients.base import MarketplaceClient, MarketplaceError
from .models import SyncJob
from .retry import call_with_retry

logger = logging.getLogger(__name__)

DEFAULT_HISTORY_DAYS = 60
STALE_JOB_AFTER = timedelta(minutes=10)


class SyncAlreadyRunning(Exception):
    pass


def _start_job(brand, triggered_by, source) -> SyncJob:
    with transaction.atomic():
        Brand.objects.select_for_update().get(pk=brand.pk)  # serialises concurrent sync requests
        running = SyncJob.objects.filter(brand=brand, status=SyncJob.Status.RUNNING)
        # A job stuck in RUNNING (e.g. the worker crashed) shouldn't block syncing forever.
        running.filter(started_at__lt=timezone.now() - STALE_JOB_AFTER).update(
            status=SyncJob.Status.FAILED, finished_at=timezone.now(), error="Timed out (marked stale)."
        )
        if running.exists():
            raise SyncAlreadyRunning("A sync is already running for this brand.")
        return SyncJob.objects.create(brand=brand, triggered_by=triggered_by, source=source)


def upsert_products(brand, catalog) -> dict[str, Product]:
    now = timezone.now()
    Product.objects.bulk_create(
        [
            Product(
                brand=brand,
                asin=item.asin,
                title=item.title,
                category=item.category,
                image_url=item.image_url,
                price=item.price,
                competitor_price=item.competitor_price,
                rating=item.rating,
                review_count=item.review_count,
                inventory_qty=item.inventory_qty,
                is_active=True,
                last_synced_at=now,
            )
            for item in catalog
        ],
        update_conflicts=True,
        unique_fields=["brand", "asin"],
        update_fields=[
            "title", "category", "image_url", "price", "competitor_price", "rating",
            "review_count", "inventory_qty", "is_active", "last_synced_at", "updated_at",
        ],
    )
    asins = [item.asin for item in catalog]
    # Listings that disappeared from the marketplace are deactivated, not deleted (keeps history).
    Product.objects.filter(brand=brand).exclude(asin__in=asins).update(is_active=False)
    return {p.asin: p for p in Product.objects.filter(brand=brand, asin__in=asins)}


def upsert_metrics(products_by_asin, records) -> int:
    rows = [
        DailyMetric(
            product=products_by_asin[r.asin],
            date=r.date,
            units=r.units,
            revenue=r.revenue,
            sessions=r.sessions,
            price=r.price,
            competitor_price=r.competitor_price,
            rating=r.rating,
            inventory_qty=r.inventory_qty,
        )
        for r in records
        if r.asin in products_by_asin
    ]
    DailyMetric.objects.bulk_create(
        rows,
        batch_size=1000,
        update_conflicts=True,
        unique_fields=["product", "date"],
        update_fields=["units", "revenue", "sessions", "price", "competitor_price", "rating", "inventory_qty"],
    )
    return len(rows)


def run_sync(brand, *, triggered_by=None, client: MarketplaceClient | None = None,
             history_days: int = DEFAULT_HISTORY_DAYS) -> SyncJob:
    """Run a full sync for one brand. Returns the SyncJob (status SUCCESS or FAILED).

    Raises SyncAlreadyRunning if another sync for the brand is in progress.
    """
    client = client or get_marketplace_client()
    job = _start_job(brand, triggered_by, client.name)
    try:
        end = timezone.localdate()
        start = end - timedelta(days=history_days - 1)

        catalog = call_with_retry(lambda: client.fetch_catalog(brand))
        asins = [item.asin for item in catalog]
        records = call_with_retry(lambda: client.fetch_daily_metrics(brand, asins, start, end))

        with transaction.atomic():
            products = upsert_products(brand, catalog)
            job.products_upserted = len(products)
            job.metrics_upserted = upsert_metrics(products, records)
            result = generate_recommendations(brand)
            job.recommendations_created = result.created
            job.recommendations_updated = result.updated
            job.recommendations_expired = result.expired

        job.status = SyncJob.Status.SUCCESS
        logger.info("Sync %s for %s finished: %d products, %d metrics", job.pk, brand, len(products), job.metrics_upserted)
    except (MarketplaceError, NotImplementedError) as exc:
        job.status = SyncJob.Status.FAILED
        job.error = str(exc)
        logger.warning("Sync %s for %s failed: %s", job.pk, brand, exc)
    except Exception as exc:  # unexpected bug: record it, then let it surface
        job.status = SyncJob.Status.FAILED
        job.error = f"Internal error: {exc.__class__.__name__}"
        job.finished_at = timezone.now()
        job.save()
        logger.exception("Sync %s for %s crashed", job.pk, brand)
        raise
    job.finished_at = timezone.now()
    job.save()
    return job
