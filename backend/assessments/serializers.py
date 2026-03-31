from rest_framework import serializers
from .models import Inspection, Evidence, EvaluationTemplate, PostProjectEvaluation, ImpactFollowUp


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


class EvaluationTemplateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')

    class Meta:
        model = EvaluationTemplate
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class PostProjectEvaluationSerializer(serializers.ModelSerializer):
    evaluated_by_name = serializers.ReadOnlyField(source='evaluated_by.username')

    class Meta:
        model = PostProjectEvaluation
        fields = '__all__'
        read_only_fields = ['evaluated_by', 'evaluated_at']


class ImpactFollowUpSerializer(serializers.ModelSerializer):
    conducted_by_name = serializers.ReadOnlyField(source='conducted_by.username')

    class Meta:
        model = ImpactFollowUp
        fields = '__all__'
