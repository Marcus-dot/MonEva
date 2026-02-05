from rest_framework import viewsets, permissions
from .models import Grievance
from .serializers import GrievanceSerializer

class GrievanceViewSet(viewsets.ModelViewSet):
    queryset = Grievance.objects.all()
    serializer_class = GrievanceSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
