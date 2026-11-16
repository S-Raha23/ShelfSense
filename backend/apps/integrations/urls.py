from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import SyncJobViewSet, SyncTriggerView

router = DefaultRouter()
router.register("sync/jobs", SyncJobViewSet, basename="sync-job")

urlpatterns = [path("sync/", SyncTriggerView.as_view(), name="sync-trigger")] + router.urls
