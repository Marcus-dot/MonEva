from django.utils import timezone
from datetime import timedelta
from indicators.models import IndicatorResult
from core.models import Notification

def scan_and_escalate_backlogs():
    """
    Finds indicator results that have been pending for more than 7 days
    and notifies project owners.
    """
    threshold = timezone.now() - timedelta(days=7)
    pending_backlog = IndicatorResult.objects.filter(
        status='SUBMITTED',
        created_at__lt=threshold
    )
    
    escalated_count = 0
    notified_users = set()
    
    for result in pending_backlog:
        project = result.target.project
        # Notify Project PM or Org Managers
        # For simplicity, we notify the project creator and assigned team
        recipients = [project.owner_org] # Or specific users if roles allow
        
        # Real implementation would find specific PMs
        # Here we'll notify the 'recorded_by' that their result is overdue for verification
        # and notify the 'assigned_team' (if exists)
        
        # For this MVP Phase 4 logic:
        # 1. Notify the project managers of the project
        # In this system, we can find users with PM role assigned to the project's org or project itself
        
        # Just notify the project creator for now as a fallback
        if project.assigned_team:
            for user in project.assigned_team.all():
                if user.id not in notified_users:
                    Notification.create_notification(
                        recipient=user,
                        title="Impact Verification Escalation",
                        message=f"Project '{project.name}' has unverified results pending for >7 days. Please review the Verification Registry.",
                        notification_type=Notification.Type.WARNING,
                        related_model='Project',
                        related_id=str(project.id)
                    )
                    notified_users.add(user.id)
                    escalated_count += 1
                    
    return escalated_count

def get_verification_backlog_score(project):
    """
    Returns a risk score contribution based on unverified results.
    """
    threshold = timezone.now() - timedelta(days=7)
    backlog_count = IndicatorResult.objects.filter(
        target__project=project,
        status='SUBMITTED',
        created_at__lt=threshold
    ).count()
    
    if backlog_count > 5:
        return 20, f"Critical verification backlog ({backlog_count} items >7 days)"
    elif backlog_count > 0:
        return 10, f"Pending verification backlog ({backlog_count} items)"
    
    return 0, ""
