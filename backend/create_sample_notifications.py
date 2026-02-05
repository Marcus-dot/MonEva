"""
Helper script to create sample notifications for testing
"""
from core.models import User, Notification
from projects.models import Project
import uuid

# Get admin user
admin = User.objects.filter(username='admin').first()

if admin:
    # Get a sample project if exists
    sample_project = Project.objects.first()
    project_id = str(sample_project.id) if sample_project else str(uuid.uuid4())
    
    # Create sample notifications with related_model and related_id
    # The action_url will be auto-generated
    
    Notification.create_notification(
        recipient=admin,
        title="Welcome to MonEva!",
        message="Your notification system is now active. You'll receive updates about projects, evaluations, and more.",
        notification_type=Notification.Type.INFO,
        action_url="/dashboard"  # Custom URL for welcome message
    )
    
    Notification.create_notification(
        recipient=admin,
        title="New Project Assigned",
        message="You have been assigned to the Water Supply Project in Lusaka.",
        notification_type=Notification.Type.TASK_ASSIGNED,
        related_model='Project',
        related_id=project_id
        # action_url will be auto-generated: /dashboard/projects/{project_id}
    )
    
    Notification.create_notification(
        recipient=admin,
        title="Evaluation Due Soon",
        message="The evaluation for Healthcare Facility Construction is due in 3 days.",
        notification_type=Notification.Type.DEADLINE_APPROACHING,
        related_model='Evaluation',
        related_id=str(uuid.uuid4())  # Using dummy ID for demo
        # action_url will be auto-generated: /dashboard/evaluations/{id}
    )
    
    Notification.create_notification(
        recipient=admin,
        title="Approval Required",
        message="Payment claim #1234 requires your approval.",
        notification_type=Notification.Type.APPROVAL_NEEDED,
        related_model='PaymentClaim',
        related_id=str(uuid.uuid4())  # Using dummy ID for demo
        # action_url will be auto-generated: /dashboard/finance/{id}
    )
    
    print(f"✅ Created 4 sample notifications for {admin.username}")
    print("   Notifications now have auto-generated action URLs based on related_model and related_id")
else:
    print("❌ Admin user not found")
