from rest_framework import viewsets, permissions
from .models import Inspection, Evidence
from .serializers import InspectionSerializer, EvidenceSerializer, PostProjectEvaluationSerializer, ImpactFollowUpSerializer

from core.permissions import IsInspector, ReadOnly

class InspectionViewSet(viewsets.ModelViewSet):
    queryset = Inspection.objects.all()
    serializer_class = InspectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsInspector | ReadOnly]

    def perform_create(self, serializer):
        # Auto-assign the inspector based on the logged-in user
        serializer.save(inspector=self.request.user)

class EvidenceViewSet(viewsets.ModelViewSet):
    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    permission_classes = [permissions.IsAuthenticated]

class PostProjectEvaluationViewSet(viewsets.ModelViewSet):
    from .models import PostProjectEvaluation
    queryset = PostProjectEvaluation.objects.all()
    serializer_class = PostProjectEvaluationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(evaluated_by=self.request.user)
        
        # Phase 12 Automation: Schedule Follow-ups?
        # Ideally we'd do this via a signal on Project.status='COMPLETED' or here.
        # For prototype, we can trigger it here or manually.

class ImpactFollowUpViewSet(viewsets.ModelViewSet):
    from .models import ImpactFollowUp
    queryset = ImpactFollowUp.objects.all()
    serializer_class = ImpactFollowUpSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset
