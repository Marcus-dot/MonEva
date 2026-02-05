from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

# Add to existing models.py

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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications')
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
    
    @classmethod
    def create_notification(cls, recipient, title, message, notification_type=Type.INFO, 
                          related_model='', related_id='', action_url=''):
        """Helper method to create notifications"""
        return cls.objects.create(
            recipient=recipient,
            type=notification_type,
            title=title,
            message=message,
            related_model=related_model,
            related_id=related_id,
            action_url=action_url
        )
