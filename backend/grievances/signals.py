"""
Django signals for automated notifications on Grievance status changes
"""
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from core.models import Notification, User
from .models import Grievance


@receiver(pre_save, sender=Grievance)
def capture_old_grievance_status(sender, instance, **kwargs):
    """Capture the old status before saving"""
    if instance.pk:
        try:
            instance._old_status = Grievance.objects.get(pk=instance.pk).status
        except Grievance.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Grievance)
def notify_on_grievance_status_change(sender, instance, created, **kwargs):
    """
    Send notifications when grievance status changes
    """
    # New grievance created
    if created:
        # Notify managers/admins
        managers = User.objects.filter(models.Q(role__is_admin=True) | models.Q(role__permissions__code='manage_projects')).distinct()
        for manager in managers:
            Notification.create_notification(
                recipient=manager,
                title="New Grievance Submitted",
                message=f"A new grievance has been submitted and requires review.",
                notification_type=Notification.Type.TASK_ASSIGNED,
                related_model='Grievance',
                related_id=str(instance.id)
            )
        return
    
    # Check if status changed
    old_status = getattr(instance, '_old_status', None)
    if old_status and old_status != instance.status:
        
        # INVESTIGATING: Notify assigned investigator
        if instance.status == 'INVESTIGATING':
            if instance.assigned_to:
                Notification.create_notification(
                    recipient=instance.assigned_to,
                    title="Grievance Assigned to You",
                    message=f"Grievance #{instance.id[:8]} has been assigned to you for investigation.",
                    notification_type=Notification.Type.TASK_ASSIGNED,
                    related_model='Grievance',
                    related_id=str(instance.id)
                )
        
        # RESOLVED: Notify external reporter via email (if contact looks like an email)
        elif instance.status == 'RESOLVED':
            contact = (instance.reporter_contact or '').strip()
            if '@' in contact:
                try:
                    from core.emails import send_plain_notification_email
                    send_plain_notification_email(
                        recipient_email=contact,
                        title='Your Grievance Has Been Resolved',
                        message=(
                            f'Your grievance (ref: {str(instance.id)[:8].upper()}) has been reviewed '
                            f'and marked as resolved. Thank you for bringing this to our attention.'
                        ),
                        action_url=None,
                    )
                except Exception:
                    import logging
                    logging.getLogger('grievances').exception(
                        'Failed to send resolution email for grievance %s', instance.id
                    )
        
        # CLOSED: Notify all stakeholders
        elif instance.status == 'CLOSED':
            # Notify assigned investigator
            if instance.assigned_to:
                Notification.create_notification(
                    recipient=instance.assigned_to,
                    title="Grievance Closed",
                    message=f"Grievance #{instance.id[:8]} has been closed.",
                    notification_type=Notification.Type.INFO,
                    related_model='Grievance',
                    related_id=str(instance.id)
                )
