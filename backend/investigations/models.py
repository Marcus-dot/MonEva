from django.db import models
from django.core.exceptions import ValidationError
from core.models import User
from projects.models import Project
from assessments.models import Inspection, Evidence
from grievances.models import Grievance
import uuid


class Investigation(models.Model):
    """
    Investigation tracking for quality issues, compliance violations, safety incidents,
    and fraud cases discovered during project monitoring.
    """
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'
    
    class Category(models.TextChoices):
        QUALITY = 'QUALITY', 'Quality Issue'
        COMPLIANCE = 'COMPLIANCE', 'Compliance Violation'
        SAFETY = 'SAFETY', 'Safety Incident'
        FRAUD = 'FRAUD', 'Suspected Fraud'
        ENVIRONMENTAL = 'ENVIRONMENTAL', 'Environmental Concern'
        GRIEVANCE = 'GRIEVANCE', 'Grievance Investigation'
        OTHER = 'OTHER', 'Other'
    
    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'
    
    # Core Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    
    # Relationships (flexible - can be linked to project, inspection, or grievance)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='investigations', null=True, blank=True)
    triggered_by_inspection = models.ForeignKey(
        Inspection, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='triggered_investigations'
    )
    related_grievance = models.ForeignKey(
        Grievance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='investigations'
    )
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_investigations')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_investigations')
    
    # Dates
    opened_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    target_resolution_date = models.DateField(null=True, blank=True)
    
    # Resolution
    resolution_summary = models.TextField(blank=True, help_text="Summary of how the investigation was resolved")
    corrective_actions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of corrective actions taken"
    )
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    estimated_impact = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated financial impact"
    )
    
    # Legacy support
    investigator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='legacy_investigations',
        help_text="Legacy field - use assigned_to instead"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        """Validate investigation data"""
        errors = {}
        
        # RESOLVED investigations must have resolution_summary
        if self.status == self.Status.RESOLVED and not self.resolution_summary:
            errors['resolution_summary'] = 'Resolution summary is required when marking as resolved'
        
        # Cannot close without resolving first
        if self.status == self.Status.CLOSED and self.resolved_at is None:
            errors['status'] = 'Investigation must be resolved before it can be closed'
        
        # Target resolution date should be in future (when creating)
        if self.target_resolution_date and not self.id:
            from django.utils import timezone
            if self.target_resolution_date < timezone.now().date():
                errors['target_resolution_date'] = 'Target resolution date should be in the future'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Auto-set resolved_at when status changes to RESOLVED
        if self.status == self.Status.RESOLVED and not self.resolved_at:
            from django.utils import timezone
            self.resolved_at = timezone.now()
        
        # Auto-set closed_at when status changes to CLOSED
        if self.status == self.Status.CLOSED and not self.closed_at:
            from django.utils import timezone
            self.closed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    class Meta:
        ordering = ['-opened_at']
        verbose_name = 'Investigation'
        verbose_name_plural = 'Investigations'


class InvestigationUpdate(models.Model):
    """
    Timeline entries for investigations - tracks all changes and notes
    """
    class UpdateType(models.TextChoices):
        NOTE = 'NOTE', 'Note Added'
        STATUS_CHANGE = 'STATUS_CHANGE', 'Status Changed'
        EVIDENCE_ADDED = 'EVIDENCE_ADDED', 'Evidence Added'
        ASSIGNMENT_CHANGE = 'ASSIGNMENT_CHANGE', 'Assignment Changed'
        RESOLUTION = 'RESOLUTION', 'Resolution Added'
        REOPENED = 'REOPENED', 'Investigation Reopened'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investigation = models.ForeignKey(Investigation, on_delete=models.CASCADE, related_name='updates')
    update_type = models.CharField(max_length=20, choices=UpdateType.choices, default=UpdateType.NOTE)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional attachments/metadata
    attachments = models.JSONField(default=list, blank=True, help_text="List of attachment file paths")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata like previous/new values")
    
    def __str__(self):
        return f"{self.get_update_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-created_at']  # Most recent first
        verbose_name = 'Investigation Update'
        verbose_name_plural = 'Investigation Updates'


class InvestigationMilestone(models.Model):
    """
    Specific milestones or tasks within an investigation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investigation = models.ForeignKey(Investigation, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if self.is_completed and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        elif not self.is_completed:
            self.completed_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {'Completed' if self.is_completed else 'Pending'}"

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'Investigation Milestone'
        verbose_name_plural = 'Investigation Milestones'


class InvestigationEvidence(models.Model):
    """
    Links Evidence items to Investigations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investigation = models.ForeignKey(Investigation, on_delete=models.CASCADE, related_name='linked_evidence')
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name='investigations', null=True, blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Notes about why this evidence is relevant")
    
    def __str__(self):
        return f"Evidence {self.evidence.id} linked to {self.investigation.title}"
    
    class Meta:
        ordering = ['-added_at']
        unique_together = ['investigation', 'evidence']
        verbose_name = 'Investigation Evidence Link'
        verbose_name_plural = 'Investigation Evidence Links'


# Keep legacy InvestigationNote for backward compatibility
class InvestigationNote(models.Model):
    """
    Legacy model - use InvestigationUpdate instead
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investigation = models.ForeignKey(Investigation, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='investigation_notes')
    note = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal notes not visible to reporters")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        author_name = self.author.username if self.author else 'Unknown'
        return f"Note by {author_name} on {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['created_at']
