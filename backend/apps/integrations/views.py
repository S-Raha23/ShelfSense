from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.tenancy import BrandScopedMixin, HasBrand, get_user_brand

from .models import SyncJob
from .serializers import SyncJobSerializer
from .services import SyncAlreadyRunning, run_sync


class SyncTriggerView(APIView):
    """Start a marketplace sync for the user's brand.

    Runs synchronously because the mock adapter finishes in well under a second. With the real
    SP-API (asynchronous reports) this view would enqueue a Celery task and return 202.
    """

    permission_classes = [HasBrand]
    throttle_scope = "sync"  # protects our third-party API quota from button-mashing

    @extend_schema(request=None, responses={201: SyncJobSerializer, 409: None, 502: SyncJobSerializer})
    def post(self, request):
        try:
            job = run_sync(get_user_brand(request.user), triggered_by=request.user)
        except SyncAlreadyRunning as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        code = status.HTTP_201_CREATED if job.status == SyncJob.Status.SUCCESS else status.HTTP_502_BAD_GATEWAY
        return Response(SyncJobSerializer(job).data, status=code)


class SyncJobViewSet(BrandScopedMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SyncJobSerializer
    permission_classes = [HasBrand]
    queryset = SyncJob.objects.select_related("triggered_by")
    ordering = ["-started_at"]
