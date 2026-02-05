from rest_framework import serializers
from .models import Grievance

class GrievanceSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    
    class Meta:
        model = Grievance
        fields = '__all__'
