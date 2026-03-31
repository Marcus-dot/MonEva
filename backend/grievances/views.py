from django.conf import settings
from rest_framework import viewsets, permissions
from rest_framework.throttling import ScopedRateThrottle
from .models import Grievance
from .serializers import GrievanceSerializer


class GrievanceSubmissionThrottle(ScopedRateThrottle):
    """Rate-limits public grievance submissions. Disable via GRIEVANCE_RATE_LIMIT_ENABLED=False."""
    scope = 'grievance'

    def allow_request(self, request, view):
        if not getattr(settings, 'GRIEVANCE_RATE_LIMIT_ENABLED', True):
            return True
        return super().allow_request(request, view)


class GrievanceViewSet(viewsets.ModelViewSet):
    queryset = Grievance.objects.all()
    serializer_class = GrievanceSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_throttles(self):
        if self.action == 'create':
            return [GrievanceSubmissionThrottle()]
        return super().get_throttles()
