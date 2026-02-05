from rest_framework import serializers
from .models import Investigation, InvestigationUpdate, InvestigationEvidence, InvestigationNote, InvestigationMilestone
from core.serializers import UserSerializer


class InvestigationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for investigation timeline updates"""
    created_by_name = serializers.SerializerMethodField()
    update_type_display = serializers.CharField(source='get_update_type_display', read_only=True)
    
    class Meta:
        model = InvestigationUpdate
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'investigation']
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}" or obj.created_by.username
        return 'System'


class InvestigationEvidenceSerializer(serializers.ModelSerializer):
    """Serializer for evidence links"""
    added_by_name = serializers.ReadOnlyField(source='added_by.username')
    evidence_file = serializers.SerializerMethodField()
    evidence_type = serializers.ReadOnlyField(source='evidence.file_type')
    
    class Meta:
        model = InvestigationEvidence
        fields = '__all__'
        read_only_fields = ['added_by', 'added_at']
    
    def get_evidence_file(self, obj):
        if obj.evidence and obj.evidence.file:
            return {
                'url': obj.evidence.file.url,
                'filename': obj.evidence.file.name.split('/')[-1]
            }
        return None


class InvestigationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    project_name = serializers.ReadOnlyField(source='project.name')
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name =serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    updates_count = serializers.SerializerMethodField()
    evidence_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Investigation
        fields = [
            'id', 'title', 'status', 'status_display', 'severity', 'severity_display',
            'category', 'category_display', 'project', 'project_name',
            'assigned_to', 'assigned_to_name', 'created_by', 'created_by_name',
            'opened_at', 'resolved_at', 'closed_at', 'target_resolution_date',
            'updates_count', 'evidence_count'
        ]
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}" or obj.assigned_to.username
        return None
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}" or obj.created_by.username
        return None
    
    def get_updates_count(self, obj):
        return obj.updates.count()
    
    def get_evidence_count(self, obj):
        return obj.linked_evidence.count()


class InvestigationMilestoneSerializer(serializers.ModelSerializer):
    """Serializer for investigation milestones"""
    class Meta:
        model = InvestigationMilestone
        fields = '__all__'
        read_only_fields = ['investigation', 'created_at', 'completed_at']


class InvestigationSerializer(serializers.ModelSerializer):
    """Full serializer with nested relationships"""
    project_name = serializers.ReadOnlyField(source='project.name')
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    inspection_details = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    # Nested relationships
    updates = InvestigationUpdateSerializer(many=True, read_only=True)
    linked_evidence = InvestigationEvidenceSerializer(many=True, read_only=True)
    milestones = InvestigationMilestoneSerializer(many=True, read_only=True)
    
    # Counts
    updates_count = serializers.SerializerMethodField()
    evidence_count = serializers.SerializerMethodField()
    milestones_count = serializers.SerializerMethodField()
    completed_milestones_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Investigation
        fields = '__all__'
        read_only_fields = ['created_by', 'opened_at', 'resolved_at', 'closed_at', 'created_at', 'updated_at']
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}" or obj.assigned_to.username
        return None
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}" or obj.created_by.username
        return None
    
    def get_inspection_details(self, obj):
        if obj.triggered_by_inspection:
            return {
                'id': obj.triggered_by_inspection.id,
                'verdict': obj.triggered_by_inspection.verdict
            }
        return None
    
    def get_updates_count(self, obj):
        return obj.updates.count()
    
    def get_evidence_count(self, obj):
        return obj.linked_evidence.count()

    def get_milestones_count(self, obj):
        return obj.milestones.count()

    def get_completed_milestones_count(self, obj):
        return obj.milestones.filter(is_completed=True).count()
    
    def validate(self, data):
        """Call model's clean() method for validation"""
        instance = Investigation(**data)
        instance.clean()
        return data


# Legacy serializers for backward compatibility
class InvestigationNoteSerializer(serializers.ModelSerializer):
    """Legacy - use InvestigationUpdateSerializer instead"""
    author_name = serializers.ReadOnlyField(source='author.username')
    
    class Meta:
        model = InvestigationNote
        fields = '__all__'
        read_only_fields = ['author', 'created_at']
