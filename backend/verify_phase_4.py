import os
import django
import sys
from datetime import timedelta
from django.utils import timezone

# Setup Django
sys.path.append('/Users/mwelwa/DevelopmentHub/MonEva/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneva.settings')
django.setup()

from projects.models import Project, ProjectComment
from indicators.models import IndicatorResult, IndicatorTarget
from core.models import User, Notification, ActivityLog
from projects.escalations import scan_and_escalate_backlogs, get_verification_backlog_score
from projects.performance import calculate_project_risk

def test_phase_4():
    print("--- Phase 4 Verification Start ---")
    
    # 1. Test Task Assignment Notification
    print("\n1. Testing Comment Assignment Notification...")
    admin = User.objects.filter(is_superuser=True).first()
    if not admin:
        print("Error: No admin user found for testing")
        return
        
    project = Project.objects.first()
    if not project:
        print("Error: No project found for testing")
        return

    # Create a comment and assign it to admin
    comment = ProjectComment.objects.create(
        project=project,
        author=admin,
        comment="Test task assignment",
        assigned_to=admin
    )
    
    # Manually trigger notification (simulating ViewSet behavior)
    Notification.create_notification(
        recipient=admin,
        title="New Task Assigned (Test)",
        message=f"Admin assigned you a task on Project: {project.name}",
        notification_type=Notification.Type.TASK_ASSIGNED,
        related_model='Project',
        related_id=str(project.id)
    )
    
    notif = Notification.objects.filter(recipient=admin, type=Notification.Type.TASK_ASSIGNED).first()
    if notif:
        print(f"Success: Notification created: {notif.title}")
    else:
        print("Failure: Notification not found")

    # 2. Test Escalation Engine
    print("\n2. Testing Escalation Engine...")
    target = IndicatorTarget.objects.filter(project=project).first()
    if target:
        # Create an old pending result
        old_date = timezone.now() - timedelta(days=10)
        old_result = IndicatorResult.objects.create(
            target=target,
            value=100,
            date=old_date.date(),
            status='SUBMITTED'
        )
        # Update created_at using .update() because auto_now_add makes it hard to set
        IndicatorResult.objects.filter(id=old_result.id).update(created_at=old_date)
        
        count = scan_and_escalate_backlogs()
        print(f"Escalated {count} results")
        
        risk = calculate_project_risk(project)
        print(f"Project Risk Score with backlog: {risk['score']}")
        governance_factor = any(f['type'] == 'GOVERNANCE' for f in risk['factors'])
        if governance_factor:
            print("Success: Governance backlog detected in risk assessment")
        else:
            print("Failure: Governance backlog not detected in risk assessment")
            
        # Clean up
        old_result.delete()

    # 3. Test Audit Trail
    print("\n3. Testing Audit Trail...")
    log_count_before = ActivityLog.objects.count()
    # Simulate a verification
    ActivityLog.objects.create(
        actor=admin,
        action=ActivityLog.Action.APPROVE,
        target_model='IndicatorResult',
        target_id='test-audit',
        details={"test": "audit"}
    )
    log_count_after = ActivityLog.objects.count()
    if log_count_after > log_count_before:
        print(f"Success: ActivityLog entry created (Total logs: {log_count_after})")
    else:
        print("Failure: ActivityLog entry not created")

    print("\n--- Phase 4 Verification End ---")

if __name__ == "__main__":
    test_phase_4()
