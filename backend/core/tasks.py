"""
Background tasks for automated notifications
"""
from django.utils import timezone
from django.db import models
from datetime import timedelta
from core.models import Notification, User
from finance.models import PaymentClaim
from grievances.models import Grievance
from projects.models import Contract, Milestone
from investigations.models import Investigation


def get_project_manager(project):
    """Helper to find the project manager from the assigned team"""
    if not project:
        return None
    # Try to find a user with Manager role in the assigned team
    manager = project.assigned_team.filter(role__name__iexact='Manager').first()
    if not manager:
        # Fallback: check if the 'manager' attribute exists (legacy/shim)
        if hasattr(project, 'manager') and project.manager and isinstance(project.manager, User):
            return project.manager
    return manager

def send_contract_expiry_reminders():
    """
    Send reminders for contracts expiring soon
    Checks for contracts expiring in 30, 60, or 90 days
    """
    now = timezone.now()
    
    # Contracts expiring in 90 days
    ninety_days = now + timedelta(days=90)
    contracts_90 = Contract.objects.filter(
        end_date__date=ninety_days.date(),
        # status='ACTIVE' # Removed status check as it might not be a field on Contract model based on file read
    )
    
    for contract in contracts_90:
        manager = get_project_manager(contract.project)
        if manager:
            Notification.create_notification(
                recipient=manager,
                title="Contract Expiring in 90 Days",
                # Access contractor.name since contractor is an Organization
                message=f"Contract with {contract.contractor.name} expires on {contract.end_date.strftime('%Y-%m-%d')}. Consider renewal planning.",
                notification_type=Notification.Type.DEADLINE_APPROACHING,
                related_model='Contract',
                related_id=str(contract.id)
            )
    
    # Contracts expiring in 60 days
    sixty_days = now + timedelta(days=60)
    contracts_60 = Contract.objects.filter(
        end_date__date=sixty_days.date()
    )
    
    for contract in contracts_60:
        manager = get_project_manager(contract.project)
        if manager:
            Notification.create_notification(
                recipient=manager,
                title="Contract Expiring in 60 Days",
                message=f"Contract with {contract.contractor.name} expires on {contract.end_date.strftime('%Y-%m-%d')}. Renewal action needed.",
                notification_type=Notification.Type.DEADLINE_APPROACHING,
                related_model='Contract',
                related_id=str(contract.id)
            )
    
    # Contracts expiring in 30 days
    thirty_days = now + timedelta(days=30)
    contracts_30 = Contract.objects.filter(
        end_date__date=thirty_days.date()
    )
    
    for contract in contracts_30:
        manager = get_project_manager(contract.project)
        if manager:
            Notification.create_notification(
                recipient=manager,
                title="Contract Expiring in 30 Days",
                message=f"URGENT: Contract with {contract.contractor.name} expires on {contract.end_date.strftime('%Y-%m-%d')}!",
                notification_type=Notification.Type.DEADLINE_APPROACHING,
                related_model='Contract',
                related_id=str(contract.id)
            )
    
    return f"Sent {contracts_90.count() + contracts_60.count() + contracts_30.count()} contract expiry reminders"


def send_milestone_deadline_reminders():
    """
    Send reminders for upcoming milestone deadlines
    Checks for milestones due in 3 days, 1 day, or Today
    """
    now = timezone.now()
    
    # 1. 3 Days Notice
    three_days = now + timedelta(days=3)
    milestones_3 = Milestone.objects.filter(
        due_date=three_days.date(),
        status__in=['PENDING', 'IN_PROGRESS']
    )
    for milestone in milestones_3:
        # Notify Project Manager (since we can't easily resolve Contractor User)
        manager = get_project_manager(milestone.contract.project)
        if manager:
            Notification.create_notification(
                recipient=manager,
                title="Milestone Deadline in 3 Days",
                message=f"Reminder: Milestone '{milestone.title}' is due in 3 days ({milestone.due_date.strftime('%Y-%m-%d')}).",
                notification_type=Notification.Type.DEADLINE_APPROACHING,
                related_model='Milestone',
                related_id=str(milestone.id)
            )

    # 2. 1 Day Notice (Tomorrow)
    one_day = now + timedelta(days=1)
    milestones_1 = Milestone.objects.filter(
        due_date=one_day.date(),
        status__in=['PENDING', 'IN_PROGRESS']
    )
    for milestone in milestones_1:
        manager = get_project_manager(milestone.contract.project)
        if manager:
            Notification.create_notification(
                recipient=manager,
                title="Milestone Due Tomorrow",
                message=f"URGENT: Milestone '{milestone.title}' is due tomorrow!",
                notification_type=Notification.Type.DEADLINE_APPROACHING,
                related_model='Milestone',
                related_id=str(milestone.id)
            )

    # 3. Due Today
    milestones_today = Milestone.objects.filter(
        due_date=now.date(),
        status__in=['PENDING', 'IN_PROGRESS']
    )
    for milestone in milestones_today:
        manager = get_project_manager(milestone.contract.project)
        if manager:
            Notification.create_notification(
                recipient=manager,
                title="Milestone Due Today",
                message=f"ACTION REQUIRED: Milestone '{milestone.title}' is due today.",
                notification_type=Notification.Type.DEADLINE_APPROACHING,
                related_model='Milestone',
                related_id=str(milestone.id)
            )
    
    return f"Sent reminders for {milestones_3.count()} (3-day), {milestones_1.count()} (1-day), and {milestones_today.count()} (today) milestones"


def send_impact_followup_reminders():
    """
    Send reminders for upcoming Impact Evaluations (Follow-ups)
    Checks for evaluations due in 3 days, 1 day, or Today
    """
    from assessments.models import ImpactFollowUp
    now = timezone.now()
    
    # 1. 3 Days Notice
    three_days = now + timedelta(days=3)
    evals_3 = ImpactFollowUp.objects.filter(
        scheduled_date=three_days.date(),
        status='PENDING'
    )
    for eval_obj in evals_3:
        manager = get_project_manager(eval_obj.project)
        if manager:
            Notification.create_notification(
                recipient=manager,
                title="Impact Evaluation in 3 Days",
                message=f"Evaluation '{eval_obj.title}' for {eval_obj.project.name} is scheduled for {eval_obj.scheduled_date}.",
                notification_type=Notification.Type.DEADLINE_APPROACHING,
                related_model='ImpactFollowUp',
                related_id=str(eval_obj.id)
            )

    # 2. 1 Day Notice
    one_day = now + timedelta(days=1)
    evals_1 = ImpactFollowUp.objects.filter(
        scheduled_date=one_day.date(),
        status='PENDING'
    )
    for eval_obj in evals_1:
        manager = get_project_manager(eval_obj.project)
        if manager:
            Notification.create_notification(
                recipient=manager,
                title="Impact Evaluation Tomorrow",
                message=f"Reminder: Evaluation '{eval_obj.title}' is scheduled for tomorrow.",
                notification_type=Notification.Type.DEADLINE_APPROACHING,
                related_model='ImpactFollowUp',
                related_id=str(eval_obj.id)
            )

    # 3. Due Today
    evals_today = ImpactFollowUp.objects.filter(
        scheduled_date=now.date(),
        status='PENDING'
    )
    for eval_obj in evals_today:
        manager = get_project_manager(eval_obj.project)
        if manager:
            Notification.create_notification(
                recipient=manager,
                title="Impact Evaluation Today",
                message=f"ACTION: Evaluation '{eval_obj.title}' is scheduled for today. Please log results.",
                notification_type=Notification.Type.DEADLINE_APPROACHING,
                related_model='ImpactFollowUp',
                related_id=str(eval_obj.id)
            )
            
    return f"Sent reminders for {evals_3.count()} (3-day), {evals_1.count()} (1-day), and {evals_today.count()} (today) evaluations"


def check_pending_approvals_escalation():
    """
    Check for items pending approval for too long and escalate
    - Payment claims pending >5 days
    - Grievances unresolved >7 days
    """
    now = timezone.now()
    escalation_count = 0
    
    # Get supervisors/managers (users with role ADMIN or MANAGER)
    supervisors = User.objects.filter(role__name__in=['ADMIN', 'MANAGER'])
    
    # Payment Claims pending >5 days
    five_days_ago = now - timedelta(days=5)
    pending_claims = PaymentClaim.objects.filter(
        status='SUBMITTED',
        created_at__lte=five_days_ago
    )
    
    for claim in pending_claims:
        days_pending = (now - claim.created_at).days
        
        # Notify all supervisors
        for supervisor in supervisors:
            Notification.create_notification(
                recipient=supervisor,
                title="Pending Approval Requires Attention",
                message=f"Payment claim #{claim.id[:8]} for ZMW {claim.amount:,.2f} has been pending for {days_pending} days. Immediate action required.",
                notification_type=Notification.Type.ESCALATION,
                related_model='PaymentClaim',
                related_id=str(claim.id)
            )
            escalation_count += 1
    
    # Grievances unresolved >7 days
    seven_days_ago = now - timedelta(days=7)
    pending_grievances = Grievance.objects.filter(
        status__in=['OPEN', 'INVESTIGATING'],
        created_at__lte=seven_days_ago
    )
    
    for grievance in pending_grievances:
        days_pending = (now - grievance.created_at).days
        
        # Notify all supervisors
        for supervisor in supervisors:
            Notification.create_notification(
                recipient=supervisor,
                title="Unresolved Grievance Requires Attention",
                message=f"Grievance #{grievance.id[:8]} has been unresolved for {days_pending} days. Immediate action required.",
                notification_type=Notification.Type.ESCALATION,
                related_model='Grievance',
                related_id=str(grievance.id)
            )
            escalation_count += 1
    
    # Investigations overdue >10 days or past target resolution date
    ten_days_ago = now - timedelta(days=10)
    overdue_investigations = Investigation.objects.filter(
        status__in=['OPEN', 'IN_PROGRESS']
    ).filter(
        models.Q(created_at__lte=ten_days_ago) | 
        models.Q(target_resolution_date__lt=now.date())
    )
    
    for investigation in overdue_investigations:
        days_total = (now - investigation.created_at).days
        message = f"Investigation '{investigation.title}' is overdue."
        if investigation.target_resolution_date and investigation.target_resolution_date < now.date():
            message = f"Investigation '{investigation.title}' has passed its target resolution date ({investigation.target_resolution_date})."
        else:
            message = f"Investigation '{investigation.title}' has been open for {days_total} days without resolution."

        for supervisor in supervisors:
            Notification.create_notification(
                recipient=supervisor,
                title="Investigation Requires Urgent Review",
                message=f"{message} Immediate action required.",
                notification_type=Notification.Type.ESCALATION,
                related_model='Investigation',
                related_id=str(investigation.id)
            )
            escalation_count += 1
    
    return f"Sent {escalation_count} escalation notifications for {pending_claims.count()} claims, {pending_grievances.count()} grievances, and {overdue_investigations.count()} investigations"


def send_daily_digests():
    """
    Send a daily summary of pending actions to users.
    Run daily at 7:00 AM.
    """
    from assessments.models import ImpactFollowUp
    
    today = timezone.now().date()
    three_days_future = today + timedelta(days=3)
    
    # Get all active users
    users = User.objects.filter(is_active=True)
    
    notifications_sent = 0
    
    for user in users:
        pending_count = 0
        details = []
        
        # 1. Pending specific approvals (Payment Claims)
        claims_to_approve = PaymentClaim.objects.filter(
            assigned_approver=user,
            status='SUBMITTED'
        ).count()
        if claims_to_approve > 0:
            pending_count += claims_to_approve
            details.append(f"{claims_to_approve} payment claims to approve")
            
        # 2. Project Manager Items
        # Milestones due soon (<= 3 days)
        # Note: Optimization would be to filter projects first, but loop is acceptable for prototype scale
        upcoming_milestones = Milestone.objects.filter(
            due_date__lte=three_days_future,
            due_date__gte=today,
            status__in=['PENDING', 'IN_PROGRESS']
        )
        
        my_milestones_count = 0
        for m in upcoming_milestones:
            pm = get_project_manager(m.contract.project)
            if pm == user:
                my_milestones_count += 1
                
        if my_milestones_count > 0:
            pending_count += my_milestones_count
            details.append(f"{my_milestones_count} milestones due soon")

        # Impact Assessments due soon
        upcoming_evals = ImpactFollowUp.objects.filter(
            scheduled_date__lte=three_days_future,
            scheduled_date__gte=today,
            status='PENDING'
        )
        
        my_evals_count = 0
        for e in upcoming_evals:
            pm = get_project_manager(e.project)
            if pm == user:
                my_evals_count += 1
        
        if my_evals_count > 0:
            pending_count += my_evals_count
            details.append(f"{my_evals_count} impact evaluations coming up")
            
        # 3. Supervisor Escalations (Admin/Manager only)
        if user.role and user.role.name in ['ADMIN', 'MANAGER']:
            # Grievances > 7 days
            overdue_grievances = Grievance.objects.filter(
                status__in=['OPEN', 'INVESTIGATING'],
                created_at__lte=timezone.now() - timedelta(days=7)
            ).count()
            
            if overdue_grievances > 0:
                pending_count += overdue_grievances
                details.append(f"{overdue_grievances} overdue grievances")
                
            # Investigations > 10 days
            overdue_investigations = Investigation.objects.filter(
                status__in=['OPEN', 'IN_PROGRESS'],
                created_at__lte=timezone.now() - timedelta(days=10)
            ).count()
            
            if overdue_investigations > 0:
                pending_count += overdue_investigations
                details.append(f"{overdue_investigations} overdue investigations")

        # SEND NOTIFICATION
        if pending_count > 0:
            summary_text = ", ".join(details)
            Notification.create_notification(
                recipient=user,
                title="Daily Digest: Actions Required",
                message=f"Good morning! You have {pending_count} items requiring attention today: {summary_text}.",
                notification_type=Notification.Type.DAILY_DIGEST
            )
            notifications_sent += 1
            
    return f"Sent daily digests to {notifications_sent} users"
