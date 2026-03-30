from rest_framework import serializers
from .models import Indicator, IndicatorTarget, IndicatorResult, LogFrameNode, FrameworkTemplate

class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicator
        fields = '__all__'

class IndicatorResultSerializer(serializers.ModelSerializer):
    recorded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = IndicatorResult
        fields = '__all__'
        read_only_fields = ('recorded_by', 'created_at', 'target')

class LogFrameNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogFrameNode
        fields = '__all__'

class IndicatorTargetSerializer(serializers.ModelSerializer):
    indicator = IndicatorSerializer(read_only=True)
    indicator_id = serializers.UUIDField(write_only=True)
    results = IndicatorResultSerializer(many=True, read_only=True)
    
    # Custom field to calculate progress
    progress_percent = serializers.SerializerMethodField()
    latest_value = serializers.SerializerMethodField()
    
    # Read-only details for frontend display
    logframe_node_details = LogFrameNodeSerializer(source='logframe_node', read_only=True)

    class Meta:
        model = IndicatorTarget
        fields = '__all__'
        extra_kwargs = {
            'logframe_node': {'required': False}
        }

    def get_latest_value(self, obj):
        if obj.indicator.unit_type == 'FORMULA' and obj.indicator.formula_definition:
            try:
                from .formula import resolve_formula
                return resolve_formula(obj.indicator.formula_definition, obj, obj.project)
            except Exception:
                return 0

        # Normal indicators: Only show VERIFIED results as current value
        latest = obj.results.filter(status='VERIFIED').first()
        return latest.value if latest else obj.baseline_value

    def get_progress_percent(self, obj):
        current = self.get_latest_value(obj)
        target = obj.target_value
        baseline = obj.baseline_value
        
        try:
            current = float(current)
            target = float(target)
            baseline = float(baseline)
            
            if target == baseline:
                return 100.0 if current >= target else 0.0

            # Handle direction (Daylight elevation)
            if obj.indicator.direction == 'DECREASING':
                # e.g. Baseline 100, Target 20, Current 60 -> Progress = (100-60)/(100-20) = 40/80 = 50%
                if baseline == target: return 0.0
                progress = (baseline - current) / (baseline - target) * 100
            else:
                progress = (current - baseline) / (target - baseline) * 100
                
            return round(max(0, progress), 2)
        except:
            return 0.0

class FrameworkTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrameworkTemplate
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')
