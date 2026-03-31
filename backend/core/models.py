from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class Permission(models.Model):
    """Individual permission that can be assigned to roles"""
    code = models.CharField(max_length=100, unique=True, help_text="e.g., 'view_dashboard', 'create_project'")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=50, help_text="e.g., 'dashboard', 'projects', 'evaluations'")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['module', 'code']
    
    def __str__(self):
        return f"{self.module}.{self.code}"

class Role(models.Model):
    """Custom roles with assigned permissions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, related_name='roles', blank=True)
    is_system_role = models.BooleanField(default=False, help_text="System roles cannot be deleted")
    is_admin = models.BooleanField(
        default=False,
        help_text="Users with this role have full system access (maker-checker bypass, admin APIs)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def has_permission(self, permission_code):
        """Check if role has a specific permission"""
        return self.permissions.filter(code=permission_code).exists()

class User(AbstractUser):
    class LegacyRoles(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        PROJECT_MANAGER = 'PM', 'Project Manager'
        INSPECTOR = 'INSPECTOR', 'Inspector'
        FINANCE = 'FINANCE', 'Finance'
        CONTRACTOR = 'CONTRACTOR', 'Contractor'
        IMPACT_ANALYST = 'IMPACT_ANALYST', 'Impact Analyst'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # New role system
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='users', null=True, blank=True)
    # Legacy role field for backward compatibility and migration
    legacy_role = models.CharField(max_length=20, choices=LegacyRoles.choices, null=True, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.role.name if self.role else 'No Role'})"
    
    @property
    def is_admin_user(self) -> bool:
        """True if the user's role has the is_admin flag set. Use this instead
        of comparing role.name strings throughout the codebase."""
        return bool(self.role and self.role.is_admin)

    def has_permission(self, permission_code):
        """Check if user has a specific permission through their role"""
        if not self.role:
            return False
        return self.role.has_permission(permission_code)

class Organization(models.Model):
    class Types(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        CONTRACTOR = 'CONTRACTOR', 'Contractor'
        PARTNER = 'PARTNER', 'Partner'
        VENDOR = 'VENDOR', 'Vendor'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=Types.choices)
    
    def __str__(self):
        return self.name

class ActivityLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'CREATE', 'Create'
        UPDATE = 'UPDATE', 'Update'
        DELETE = 'DELETE', 'Delete'
        LOGIN = 'LOGIN', 'Login'
        APPROVE = 'APPROVE', 'Approve'
        REJECT = 'REJECT', 'Reject'
        COMMENT = 'COMMENT', 'Comment'
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='logs')
    action = models.CharField(max_length=20, choices=Action.choices)
    
    target_model = models.CharField(max_length=50, help_text="e.g. Project, PaymentClaim")
    target_id = models.CharField(max_length=100, help_text="UUID string of target")
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.actor} executed {self.action} on {self.target_model}"

class DashboardPreference(models.Model):
    """User preferences for dashboard customization"""
    TIME_RANGE_CHOICES = [
        ('7d', 'Last 7 Days'),
        ('30d', 'Last 30 Days'),
        ('90d', 'Last 90 Days'),
        ('1y', 'Last Year'),
        ('all', 'All Time'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_pref')
    hidden_widgets = models.JSONField(default=list, help_text="List of widget IDs to hide")
    time_range = models.CharField(max_length=10, choices=TIME_RANGE_CHOICES, default='30d')
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dashboard prefs for {self.user.username}"
    
    class Meta:
        verbose_name = 'Dashboard Preference'
        verbose_name_plural = 'Dashboard Preferences'

class Notification(models.Model):
    """User notifications for system events"""
    class Type(models.TextChoices):
        INFO = 'INFO', 'Information'
        SUCCESS = 'SUCCESS', 'Success'
        WARNING = 'WARNING', 'Warning'
        ERROR = 'ERROR', 'Error'
        TASK_ASSIGNED = 'TASK_ASSIGNED', 'Task Assigned'
        COMMENT_ADDED = 'COMMENT_ADDED', 'Comment Added'
        STATUS_CHANGED = 'STATUS_CHANGED', 'Status Changed'
        APPROVAL_NEEDED = 'APPROVAL_NEEDED', 'Approval Needed'
        DEADLINE_APPROACHING = 'DEADLINE_APPROACHING', 'Deadline Approaching'
        DAILY_DIGEST = 'DAILY_DIGEST', 'Daily Digest'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=Type.choices, default=Type.INFO)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Link to related object
    related_model = models.CharField(max_length=50, blank=True, help_text="e.g., 'Project', 'Inspection'")
    related_id = models.CharField(max_length=100, blank=True, help_text="UUID of related object")
    action_url = models.CharField(max_length=500, blank=True, help_text="URL to navigate when clicked")
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def generate_action_url(self):
        """Generate action URL based on related model and ID"""
        if not self.related_model or not self.related_id:
            return ''
        
        # Map model names to their detail page URLs
        url_mapping = {
            'PaymentClaim': f'/dashboard/finance/{self.related_id}',
            # Evaluations live inside the project sustainability/inspections tabs
            'Evaluation': '/dashboard/projects/',
            'PostProjectEvaluation': '/dashboard/projects/',
            'ImpactFollowUp': '/dashboard/projects/',
            'Project': f'/dashboard/projects/{self.related_id}',
            'Investigation': f'/dashboard/investigations/{self.related_id}',
            'Grievance': f'/dashboard/grievances/{self.related_id}',
            # Contracts live inside the project contracts tab
            'Contract': '/dashboard/projects/',
            'Milestone': '/dashboard/projects/',
            'Inspection': f'/dashboard/inspections/{self.related_id}',
        }
        
        return url_mapping.get(self.related_model, '')
    
    @classmethod
    def create_notification(cls, recipient, title, message, notification_type=Type.INFO,
                          related_model='', related_id='', action_url=''):
        """Helper method to create notifications and trigger email"""
        # Auto-generate action_url if not provided but related_model/id exist
        if not action_url and related_model and related_id:
            temp_notif = cls(related_model=related_model, related_id=related_id)
            action_url = temp_notif.generate_action_url()

        notification = cls.objects.create(
            recipient=recipient,
            type=notification_type,
            title=title,
            message=message,
            related_model=related_model,
            related_id=related_id,
            action_url=action_url
        )

        # Also send email if recipient has an email address
        if recipient.email:
            try:
                from core.emails import send_plain_notification_email
                send_plain_notification_email(
                    recipient_email=recipient.email,
                    recipient_name=recipient.get_full_name() or recipient.username,
                    title=title,
                    message=message,
                    action_url=action_url,
                    notification_type=notification_type
                )
            except Exception:
                pass  # Never break notification creation due to email failure

        return notification

class ScheduledReport(models.Model):
    """Configuration for automated report delivery"""
    class Frequency(models.TextChoices):
        DAILY = 'DAILY', 'Daily'
        WEEKLY = 'WEEKLY', 'Weekly'
        MONTHLY = 'MONTHLY', 'Monthly'

    class Format(models.TextChoices):
        CSV = 'CSV', 'CSV'
        XLSX = 'XLSX', 'Excel'
        PDF = 'PDF', 'PDF'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_reports')
    report_type = models.CharField(max_length=50, help_text="e.g. 'portfolio', 'financial', 'impact'")
    report_name = models.CharField(max_length=255)
    
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.WEEKLY)
    format = models.CharField(max_length=10, choices=Format.choices, default=Format.PDF)
    
    recipients = models.JSONField(default=list, help_text="List of email addresses")
    filters = models.JSONField(default=dict, blank=True, help_text="Filter criteria for the report")
    
    last_sent_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_name} ({self.frequency}) for {self.user.username}"

    class Meta:
        ordering = ['next_run_at']

class EmailLog(models.Model):
    """Track all email sends for audit and retry"""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'
        BOUNCED = 'BOUNCED', 'Bounced'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.EmailField()
    notification_type = models.CharField(max_length=50)  # grievance_opened, contract_expiry, etc.
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['recipient', 'status'])]

    def __str__(self):
        return f"{self.notification_type} to {self.recipient} ({self.status})"


class Document(models.Model):
    """Centralized document store — any file attached to any object in the system."""

    class Category(models.TextChoices):
        CONTRACT = 'CONTRACT', 'Contract'
        REPORT = 'REPORT', 'Report'
        EVALUATION = 'EVALUATION', 'Evaluation'
        FINANCIAL = 'FINANCIAL', 'Financial'
        LEGAL = 'LEGAL', 'Legal'
        PHOTO = 'PHOTO', 'Photo'
        CORRESPONDENCE = 'CORRESPONDENCE', 'Correspondence'
        OTHER = 'OTHER', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/%Y/%m/')
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")

    # Optional links — a document can belong to a project, contract, or both
    project = models.ForeignKey(
        'projects.Project', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents'
    )
    contract = models.ForeignKey(
        'projects.Contract', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents'
    )

    # Visibility
    is_public = models.BooleanField(
        default=False,
        help_text="Public documents appear on the transparency page"
    )

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='documents')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'category']),
            models.Index(fields=['is_public']),
        ]

    def __str__(self):
        return f"{self.name} ({self.category})"

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None

    @property
    def file_extension(self):
        if self.file:
            import os
            return os.path.splitext(self.file.name)[1].lower()
        return ''
