from rest_framework import serializers
from .models import ExternalMapLayer

class ExternalMapLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalMapLayer
        fields = ['id', 'name', 'layer_type', 'url', 'attribution', 'is_active']
