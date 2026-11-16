from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from rest_framework.test import APIClient

from apps.catalog.models import DailyMetric
from apps.integrations.clients.mock import MockAmazonClient
from apps.integrations.services import run_sync
from apps.recommendations.engine import generate_recommendations
from apps.recommendations.models import Recommendation


def test_register_creates_user_and_brand_and_returns_tokens(db):
    res = APIClient().post(
        "/api/auth/register/",
        {"username": "carol", "password": "Str0ng-pass-99", "brand_name": "Gamma Home"},
        format="json",
    )
    assert res.status_code == 201
    assert res.data["user"]["brand"]["slug"] == "gamma-home"
    assert res.data["access"] and res.data["refresh"]


def test_login_returns_jwt_pair(member):
    res = APIClient().post("/api/auth/token/", {"username": "alice", "password": "pass-12345-word"}, format="json")
    assert res.status_code == 200 and "access" in res.data


def test_endpoints_require_authentication(db):
    assert APIClient().get("/api/products/").status_code == 401


def test_brand_isolation(api, synced_brand, other_member):
    """A user must never see another brand's products, recommendations or sync jobs."""
    user_b, brand_b = other_member
    run_sync(brand_b, client=MockAmazonClient(failure_rate=0))
    other_product = brand_b.products.first()
    other_rec = Recommendation.objects.filter(brand=brand_b).first()

    product_ids = {p["id"] for p in api.get("/api/products/").data["results"]}
    assert other_product.id not in product_ids
    assert api.get(f"/api/products/{other_product.id}/").status_code == 404
    assert api.get(f"/api/recommendations/{other_rec.id}/").status_code == 404
    assert api.post(f"/api/recommendations/{other_rec.id}/dismiss/").status_code == 404


def test_product_list_revenue_is_not_inflated_by_joins(api, synced_brand):
    """Regression test: annotating open recommendation counts must not multiply revenue sums."""
    rows = api.get("/api/products/?days=30").data["results"]
    product_with_rec = next(p for p in rows if p["open_recommendations"] > 0)
    summary = api.get("/api/dashboard/summary/?days=30").data
    assert Decimal(summary["revenue"]) == sum(Decimal(p["revenue_period"]) for p in rows)
    assert product_with_rec["revenue_period"]


def test_dashboard_summary_matches_database(api, synced_brand):
    data = api.get("/api/dashboard/summary/?days=30").data
    last_day = DailyMetric.objects.filter(product__brand=synced_brand).latest("date").date
    db_revenue = DailyMetric.objects.filter(
        product__brand=synced_brand, date__gte=last_day - timedelta(days=29)
    ).aggregate(s=Sum("revenue"))["s"]
    assert Decimal(data["revenue"]) == db_revenue
    assert data["active_products"] == 12
    assert data["change"]["revenue"] is not None


def test_period_validation(api, synced_brand):
    assert api.get("/api/dashboard/summary/?days=500").status_code == 400
    assert len(api.get("/api/dashboard/timeseries/?days=28&granularity=week").data) <= 5


def test_dismiss_snoozes_rule_for_cooldown(api, synced_brand):
    rec = Recommendation.objects.filter(brand=synced_brand, status="open").first()
    res = api.post(f"/api/recommendations/{rec.id}/dismiss/")
    assert res.status_code == 200 and res.data["status"] == "dismissed"
    assert api.post(f"/api/recommendations/{rec.id}/dismiss/").status_code == 409

    generate_recommendations(synced_brand)
    assert not Recommendation.objects.filter(product=rec.product, rule_code=rec.rule_code, status="open").exists()


def test_sync_endpoint_runs_and_lists_jobs(api, member):
    res = api.post("/api/sync/")
    assert res.status_code == 201 and res.data["status"] == "success"
    jobs = api.get("/api/sync/jobs/").data
    assert jobs["count"] == 1


def test_recommendation_summary(api, synced_brand):
    data = api.get("/api/recommendations/summary/").data
    assert data["open_total"] == data["high"] + data["medium"] + data["low"] == 8
    assert set(data["by_category"]) == {"inventory", "pricing", "listing"}
