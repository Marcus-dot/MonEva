from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from projects.models import Project
from core.models import User, Notification, Role
import uuid

# ... (omitted class Grievance code) ...



class Grievance(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        INVESTIGATING = 'INVESTIGATING', 'Investigating'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='grievances')
    reporter_contact = models.CharField(max_length=255, help_text="Email or Phone")
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_grievances')
    resolution_date = models.DateField(null=True, blank=True)
    resolution_summary = models.TextField(blank=True, help_text="Explanation of how the grievance was resolved")
    
    # Impact Accountability
    resolution_impact_score = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Score (1-5) on how effectively the resolution improved community conditions"
    )
    impact_verification_date = models.DateTimeField(null=True, blank=True)
    impact_analyst_notes = models.TextField(blank=True, help_text="Notes from Impact Analyst verification")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Grievance {self.id} - {self.status}"

# Signals
from django.db.models.signals import post_save
from django.dispatch import receiver
from projects.automation import sync_grievance_to_indicator

@receiver(post_save, sender=Grievance)
def grievance_sync_handler(sender, instance, **kwargs):
    sync_grievance_to_indicator(instance)

@receiver(post_save, sender=Grievance)
def grievance_impact_notification(sender, instance, **kwargs):
    """
    Notify Impact Analysts when a grievance is resolved to verify impact.
    """
    if instance.status == Grievance.Status.RESOLVED:
        # Check if we already notified (optimization: could check earlier notifications)
        # For now, we assume resolution is a distinct event worth notifying.
        
        # Find Analysts
        analysts = User.objects.filter(role__name='IMPACT_ANALYST')
        if not analysts.exists():
            # Fallback to Admin
            analysts = User.objects.filter(role__name='ADMIN')
            
        for analyst in analysts:
            Notification.create_notification(
                recipient=analyst,
                title="Grievance Resolved - Impact Verification Needed",
                message=f"Grievance #{str(instance.id)[:8]} has been resolved. Please verify the community impact.",
                notification_type=Notification.Type.TASK_ASSIGNED,
                related_model='Grievance',
                related_id=str(instance.id)
            )
