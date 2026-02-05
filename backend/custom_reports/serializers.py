from rest_framework import serializers
from .models import CustomReport

class CustomReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomReport
        fields = ['id', 'title', 'description', 'layout_config', 'created_by', 'created_at', 'updated_at', 'is_public']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)
