from rest_framework import viewsets, permissions, status as http_status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
import logging
from core.models import ActivityLog
from .models import Investigation, InvestigationUpdate, InvestigationEvidence, InvestigationNote, InvestigationMilestone
from .serializers import (
    InvestigationSerializer,
    InvestigationListSerializer,
    InvestigationUpdateSerializer,
    InvestigationEvidenceSerializer,
    InvestigationNoteSerializer,
    InvestigationMilestoneSerializer
)


class InvestigationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing investigations with filtering and custom actions
    """
    queryset = Investigation.objects.select_related(
        'project', 'assigned_to', 'created_by', 'triggered_by_inspection'
    ).prefetch_related('updates', 'linked_evidence')
    permission_classes = [permissions.IsAuthenticated]
    
    # Add pagination
    from rest_framework.pagination import PageNumberPagination
    class StandardPagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'
        max_page_size = 100
        
    pagination_class = StandardPagination
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'severity', 'category', 'project', 'assigned_to']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['opened_at', 'severity', 'status', 'target_resolution_date']
    ordering = ['-opened_at']
    
    def get_serializer_class(self):
        """Use lighter serializer for list view"""
        if self.action == 'list':
            return InvestigationListSerializer
        return InvestigationSerializer
    
    def perform_create(self, serializer):
        """Auto-set created_by to current user"""
        investigation = serializer.save(created_by=self.request.user)
        
        # Create initial timeline entry
        InvestigationUpdate.objects.create(
            investigation=investigation,
            update_type=InvestigationUpdate.UpdateType.NOTE,
            content=f"Investigation opened: {investigation.title}",
            created_by=self.request.user
        )

        # Log Activity
        ActivityLog.objects.create(
            actor=self.request.user,
            action=ActivityLog.Action.CREATE,
            target_model='Investigation',
            target_id=str(investigation.id),
            details={
                'title': investigation.title,
                'project': str(investigation.project.id) if investigation.project else None
            },
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    @action(detail=True, methods=['post'])
    def add_update(self, request, pk=None):
        """Add a timeline update/note to investigation"""
        investigation = self.get_object()
        serializer = InvestigationUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                investigation=investigation,
                created_by=request.user
            )
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def link_evidence(self, request, pk=None):
        """Link evidence to investigation"""
        investigation = self.get_object()
        evidence_id = request.data.get('evidence_id')
        notes = request.data.get('notes', '')
        
        if not evidence_id:
            return Response(
                {'error': 'evidence_id is required'},
                status=http_status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from assessments.models import Evidence
            evidence = Evidence.objects.get(id=evidence_id)
            
            link, created = InvestigationEvidence.objects.get_or_create(
                investigation=investigation,
                evidence=evidence,
                defaults={
                    'added_by': request.user,
                    'notes': notes
                }
            )
            
            if created:
                # Create timeline entry
                InvestigationUpdate.objects.create(
                    investigation=investigation,
                    update_type=InvestigationUpdate.UpdateType.EVIDENCE_ADDED,
                    content=f"Evidence linked: {evidence.file.name}",
                    created_by=request.user
                )
            
            serializer = InvestigationEvidenceSerializer(link)
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        
        except Evidence.DoesNotExist:
            return Response(
                {'error': 'Evidence not found'},
                status=http_status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change investigation status"""
        investigation = self.get_object()
        new_status = request.data.get('status')
        note = request.data.get('note', '')
        
        if not new_status or new_status not in dict(Investigation.Status.choices):
            return Response(
                {'error': 'Invalid status'},
                status=http_status.HTTP_400_BAD_REQUEST
            )
        
        old_status = investigation.get_status_display()
        investigation.status = new_status
        investigation.save()
        
        # Create timeline entry
        InvestigationUpdate.objects.create(
            investigation=investigation,
            update_type=InvestigationUpdate.UpdateType.STATUS_CHANGE,
            content=note or f"Status changed from {old_status} to {investigation.get_status_display()}",
            created_by=request.user,
            metadata={
                'old_status': old_status,
                'new_status': investigation.get_status_display()
            }
        )
        
        # Log Activity
        ActivityLog.objects.create(
            actor=request.user,
            action=ActivityLog.Action.UPDATE,
            target_model='Investigation',
            target_id=str(investigation.id),
            details={
                'change': 'STATUS_CHANGE',
                'old_status': old_status,
                'new_status': investigation.get_status_display()
            },
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        serializer = self.get_serializer(investigation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark investigation as resolved"""
        investigation = self.get_object()
        resolution_summary = request.data.get('resolution_summary', '')
        corrective_actions = request.data.get('corrective_actions', [])
        
        if not resolution_summary:
            return Response(
                {'error': 'resolution_summary is required'},
                status=http_status.HTTP_400_BAD_REQUEST
            )
        
        investigation.status = Investigation.Status.RESOLVED
        investigation.resolution_summary = resolution_summary
        investigation.corrective_actions = corrective_actions
        investigation.resolved_at = timezone.now()
        investigation.save()
        
        # Create timeline entry
        InvestigationUpdate.objects.create(
            investigation=investigation,
            update_type=InvestigationUpdate.UpdateType.RESOLUTION,
            content=resolution_summary,
            created_by=request.user
        )
        
        # Log Activity
        ActivityLog.objects.create(
            actor=request.user,
            action=ActivityLog.Action.UPDATE,
            target_model='Investigation',
            target_id=str(investigation.id),
            details={'change': 'RESOLVED'},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        serializer = self.get_serializer(investigation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close investigation (must be resolved first)"""
        investigation = self.get_object()
        
        if investigation.status != Investigation.Status.RESOLVED:
            return Response(
                {'error': 'Investigation must be resolved before closing'},
                status=http_status.HTTP_400_BAD_REQUEST
            )
        
        investigation.status = Investigation.Status.CLOSED
        investigation.closed_at = timezone.now()
        investigation.save()
        
        # Create timeline entry
        InvestigationUpdate.objects.create(
            investigation=investigation,
            update_type=InvestigationUpdate.UpdateType.STATUS_CHANGE,
            content="Investigation closed",
            created_by=request.user
        )
        
        # Log Activity
        ActivityLog.objects.create(
            actor=request.user,
            action=ActivityLog.Action.UPDATE,
            target_model='Investigation',
            target_id=str(investigation.id),
            details={'change': 'CLOSED'},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        serializer = self.get_serializer(investigation)
        return Response(serializer.data)


    @action(detail=True, methods=['post'])
    def add_milestone(self, request, pk=None):
        """Add a milestone to investigation"""
        investigation = self.get_object()
        serializer = InvestigationMilestoneSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(investigation=investigation)
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='toggle_milestone/(?P<milestone_id>[^/.]+)')
    def toggle_milestone(self, request, pk=None, milestone_id=None):
        """Mark a milestone as complete/incomplete"""
        try:
            milestone = InvestigationMilestone.objects.get(id=milestone_id, investigation_id=pk)
            milestone.is_completed = not milestone.is_completed
            milestone.save()
            
            # Create timeline entry
            InvestigationUpdate.objects.create(
                investigation=milestone.investigation,
                update_type=InvestigationUpdate.UpdateType.NOTE,
                content=f"Milestone {'completed' if milestone.is_completed else 'reopened'}: {milestone.title}",
                created_by=request.user
            )
            
            serializer = InvestigationMilestoneSerializer(milestone)
            return Response(serializer.data)
        except InvestigationMilestone.DoesNotExist:
            return Response({'error': 'Milestone not found'}, status=http_status.HTTP_404_NOT_FOUND)


class InvestigationUpdateViewSet(viewsets.ModelViewSet):
    """ViewSet for investigation timeline updates"""
    queryset = InvestigationUpdate.objects.select_related('investigation', 'created_by')
    serializer_class = InvestigationUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['investigation', 'update_type', 'created_by']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class InvestigationMilestoneViewSet(viewsets.ModelViewSet):
    """ViewSet for managing investigation milestones"""
    queryset = InvestigationMilestone.objects.all()
    serializer_class = InvestigationMilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['investigation', 'is_completed']
    ordering = ['order', 'created_at']


class InvestigationEvidenceViewSet(viewsets.ModelViewSet):
    """ViewSet for investigation evidence links"""
    queryset = InvestigationEvidence.objects.select_related('investigation', 'evidence', 'added_by')
    serializer_class = InvestigationEvidenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['investigation']
    ordering = ['-added_at']
    
    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)


# Legacy viewsets for backward compatibility
class InvestigationNoteViewSet(viewsets.ModelViewSet):
    """Legacy - use InvestigationUpdateViewSet instead"""
    queryset = InvestigationNote.objects.all()
    serializer_class = InvestigationNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        investigation_id = self.request.query_params.get('investigation')
        if investigation_id:
            queryset = queryset.filter(investigation_id=investigation_id)
        return queryset
