from rest_framework import serializers
from .models import User, Organization, ActivityLog, DashboardPreference, Permission, Role, Notification, ScheduledReport


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model"""
    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'description', 'module', 'created_at']
        read_only_fields = ['id', 'created_at']


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model with permissions"""
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Permission.objects.all(),
        write_only=True,
        required=False,
        source='permissions'
    )
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'permission_ids', 
                  'is_system_role', 'user_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_count']
    
    def get_user_count(self, obj):
        """Get count of users with this role"""
        return obj.users.count()
    
    def validate_name(self, value):
        """Prevent modification of system role names"""
        if self.instance and self.instance.is_system_role:
            if self.instance.name != value:
                raise serializers.ValidationError("Cannot rename system roles")
        return value


class UserSerializer(serializers.ModelSerializer):
    role_details = RoleSerializer(source='role', read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        write_only=True,
        required=False,
        source='role'
    )
    password = serializers.CharField(write_only=True, required=False)
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'role', 'role_details', 'role_id', 'permissions', 'legacy_role',
                  'is_active', 'is_staff', 'date_joined', 'password']
        read_only_fields = ['id', 'date_joined', 'permissions']
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = super().create(validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance
    
    def get_permissions(self, obj):
        """Get list of permission codes for this user"""
        if obj.role:
            return list(obj.role.permissions.values_list('code', flat=True))
        return []


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'


class ActivityLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = ['id', 'actor', 'actor_name', 'action', 'target_model', 
                  'target_id', 'ip_address', 'details', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class DashboardPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardPreference
        fields = ['user', 'hidden_widgets', 'time_range', 'updated_at']
        read_only_fields = ['updated_at']

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for user notifications"""
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'message', 'related_model', 'related_id', 
                  'action_url', 'is_read', 'created_at', 'read_at', 'time_ago']
        read_only_fields = ['id', 'created_at', 'read_at', 'time_ago']
    
    def get_time_ago(self, obj):
        """Get human-readable time difference"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days}d ago"
        else:
            return obj.created_at.strftime('%b %d')

class ScheduledReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledReport
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'last_sent_at']
