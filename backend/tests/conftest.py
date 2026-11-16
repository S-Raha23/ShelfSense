import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.models import Brand, Profile
from apps.integrations.clients.mock import MockAmazonClient
from apps.integrations.services import run_sync


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    cache.clear()


def make_member(username, brand_name):
    brand = Brand.objects.create(name=brand_name, slug=brand_name.lower().replace(" ", "-"))
    user = get_user_model().objects.create_user(username=username, password="pass-12345-word")
    Profile.objects.create(user=user, brand=brand)
    return user, brand


@pytest.fixture
def member(db):
    return make_member("alice", "Alpha Goods")


@pytest.fixture
def other_member(db):
    return make_member("bob", "Beta Brands")


@pytest.fixture
def api(member):
    client = APIClient()
    client.force_authenticate(member[0])
    return client


@pytest.fixture
def synced_brand(member):
    user, brand = member
    run_sync(brand, triggered_by=user, client=MockAmazonClient(failure_rate=0))
    return brand
