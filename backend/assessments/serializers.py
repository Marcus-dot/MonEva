from rest_framework import serializers
from .models import Inspection, Evidence

class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = '__all__'

class InspectionSerializer(serializers.ModelSerializer):
    evidence = EvidenceSerializer(many=True, read_only=True)
    milestone_title = serializers.ReadOnlyField(source='milestone.title')
    inspector_username = serializers.ReadOnlyField(source='inspector.username')
    
    class Meta:
        model = Inspection
        fields = '__all__'

class PostProjectEvaluationSerializer(serializers.ModelSerializer):
    evaluated_by_name = serializers.ReadOnlyField(source='evaluated_by.username')

    class Meta:
        from .models import PostProjectEvaluation
        model = PostProjectEvaluation
        fields = '__all__'
        read_only_fields = ['evaluated_by', 'evaluated_at']

class ImpactFollowUpSerializer(serializers.ModelSerializer):
    conducted_by_name = serializers.ReadOnlyField(source='conducted_by.username')

    class Meta:
        from .models import ImpactFollowUp
        model = ImpactFollowUp
        fields = '__all__'
