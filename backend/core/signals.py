from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from .models import ActivityLog, User
from projects.models import Project
from assessments.models import Inspection
# Avoid circular import with finance if possible, or lazy import in function
# from finance.models import PaymentClaim (Will do inside function if needed or handle generic)

import json

# List of models to track
TRACKED_MODELS = {
    'Project': Project,
    'Inspection': Inspection,
    # PaymentClaim handled dynamically or imported carefully
}

def get_request_user():
    # Helper to get user from thread local if we implemented middleware
    # For now, we might rely on the 'actor' being passed explicitly or 
    # capturing it from a custom signal. 
    # MVP approach: We will inspect the 'instance' to see if it has a 'modified_by' field 
    # OR we just log the action and fill actor if available.
    # Actually, DRF views inject user. Signals don't always have access to Request.
    # Better approach for Audit: Override ViewSet perform_create/update.
    # BUT, specific requirement was "Signals".
    # Let's try to grab 'prepared_by' or 'inspector' fields if they exist.
    return None

@receiver(post_save, sender=Project)
def log_project_save(sender, instance, created, **kwargs):
    action = ActivityLog.Action.CREATE if created else ActivityLog.Action.UPDATE
    # Try to find an actor (Project doesn't have modified_by yet, but let's log system event)
    # In a real app we'd use CUserMiddleware
    ActivityLog.objects.create(
        actor=None, # System or Unknown for now
        action=action,
        target_model='Project',
        target_id=str(instance.id),
        details={'name': instance.name, 'status': instance.status}
    )

@receiver(post_delete, sender=Project)
def log_project_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        actor=None,
        action=ActivityLog.Action.DELETE,
        target_model='Project',
        target_id=str(instance.id),
        details={'name': instance.name}
    )

# Login Signals
from django.contrib.auth.signals import user_logged_in, user_login_failed

@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    ActivityLog.objects.create(
        actor=user,
        action=ActivityLog.Action.LOGIN,
        target_model='User',
        target_id=str(user.id),
        ip_address=ip,
        details={'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown')}
    )

# Email Notification Signals
from .models import Notification
from .emails import EmailTemplates
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Notification)
def send_notification_email(sender, instance, created, **kwargs):
    """
    Automatically send email when a notification is created.
    Only sends if email is configured and recipient has email address.
    """
    if not created:
        return  # Only on creation, not updates

    if not instance.recipient or not instance.recipient.email:
        logger.warning(f"Cannot send email for notification {instance.id}: recipient has no email")
        return

    try:
        recipient_name = instance.recipient.get_full_name() or instance.recipient.username
        context = {
            'recipient_name': recipient_name,
            'subject': instance.title,
            'message': instance.message,
            'action_url': instance.action_url,
        }

        # Determine template type based on notification type
        template_mapping = {
            Notification.Type.TASK_ASSIGNED: 'task_assigned',
            Notification.Type.APPROVAL_NEEDED: 'claim_pending_approval',
            Notification.Type.DEADLINE_APPROACHING: 'milestone_deadline',
            Notification.Type.STATUS_CHANGED: 'grievance_status_change',
        }

        template_type = template_mapping.get(instance.type, 'grievance_opened')

        # Send email
        success = EmailTemplates.send_notification_email(
            recipient_email=instance.recipient.email,
            notification_type=template_type,
            context=context
        )

        if not success:
            logger.error(f"Failed to send email for notification {instance.id}")

    except Exception as e:
        logger.error(f"Error in send_notification_email signal for {instance.id}: {str(e)}")
