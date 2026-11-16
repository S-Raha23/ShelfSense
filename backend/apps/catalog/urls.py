from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DashboardSummaryView, DashboardTimeseriesView, DashboardTopProductsView, ProductViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")

urlpatterns = [
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("dashboard/timeseries/", DashboardTimeseriesView.as_view(), name="dashboard-timeseries"),
    path("dashboard/top-products/", DashboardTopProductsView.as_view(), name="dashboard-top-products"),
] + router.urls
