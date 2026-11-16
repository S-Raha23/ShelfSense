from datetime import timedelta

import pytest
from django.utils import timezone

from apps.catalog.models import DailyMetric, Product
from apps.integrations.clients.base import MarketplaceError, TransientMarketplaceError
from apps.integrations.clients.mock import MockAmazonClient
from apps.integrations.models import SyncJob
from apps.integrations.retry import call_with_retry
from apps.integrations.services import SyncAlreadyRunning, run_sync
from apps.recommendations.models import Recommendation


def test_sync_populates_catalog_metrics_and_recommendations(synced_brand):
    assert Product.objects.filter(brand=synced_brand).count() == 12
    assert DailyMetric.objects.filter(product__brand=synced_brand).count() == 12 * 60
    rules_fired = set(Recommendation.objects.filter(brand=synced_brand).values_list("rule_code", flat=True))
    assert rules_fired == {"low_stock", "overstock", "price_gap", "rating_drop", "low_conversion"}
    job = SyncJob.objects.get(brand=synced_brand)
    assert job.status == SyncJob.Status.SUCCESS and job.finished_at


def test_sync_is_idempotent(synced_brand):
    counts = (Product.objects.count(), DailyMetric.objects.count(), Recommendation.objects.count())
    job = run_sync(synced_brand, client=MockAmazonClient(failure_rate=0))
    assert (Product.objects.count(), DailyMetric.objects.count(), Recommendation.objects.count()) == counts
    assert job.recommendations_created == 0 and job.recommendations_updated == counts[2]


def test_failed_sync_is_recorded_and_keeps_existing_data(synced_brand):
    class BrokenClient(MockAmazonClient):
        def fetch_daily_metrics(self, *args, **kwargs):
            raise MarketplaceError("401 Unauthorized: invalid refresh token")

    before = DailyMetric.objects.count()
    job = run_sync(synced_brand, client=BrokenClient(failure_rate=0))
    assert job.status == SyncJob.Status.FAILED
    assert "invalid refresh token" in job.error
    assert DailyMetric.objects.count() == before


def test_concurrent_sync_is_rejected_but_stale_job_is_not_blocking(member):
    _, brand = member
    job = SyncJob.objects.create(brand=brand, status=SyncJob.Status.RUNNING)
    with pytest.raises(SyncAlreadyRunning):
        run_sync(brand, client=MockAmazonClient(failure_rate=0))

    SyncJob.objects.filter(pk=job.pk).update(started_at=timezone.now() - timedelta(hours=1))
    assert run_sync(brand, client=MockAmazonClient(failure_rate=0)).status == SyncJob.Status.SUCCESS
    job.refresh_from_db()
    assert job.status == SyncJob.Status.FAILED


def test_retry_recovers_from_transient_errors():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise TransientMarketplaceError("429")
        return "ok"

    delays = []
    assert call_with_retry(flaky, sleep=delays.append) == "ok"
    assert calls["n"] == 3 and len(delays) == 2 and delays[1] > delays[0]


def test_retry_gives_up_and_does_not_retry_permanent_errors():
    with pytest.raises(TransientMarketplaceError):
        call_with_retry(lambda: (_ for _ in ()).throw(TransientMarketplaceError("429")), attempts=3, sleep=lambda s: None)

    calls = {"n": 0}

    def bad_request():
        calls["n"] += 1
        raise MarketplaceError("400")

    with pytest.raises(MarketplaceError):
        call_with_retry(bad_request, sleep=lambda s: None)
    assert calls["n"] == 1
