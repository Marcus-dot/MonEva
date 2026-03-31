from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import PaymentClaim
from .ml import scorer
from core.models import Notification, User

@receiver(post_save, sender=PaymentClaim)
def score_payment_claim(sender, instance, created, **kwargs):
    """
    Trigger AI Risk Scoring when a claim is submitted.
    """
    if instance.status == PaymentClaim.Status.SUBMITTED and instance.risk_score is None:
        try:
            print(f"--- ML: Scoring Claim {instance.id} ---")
            # 1. Train Model (Ideally async or scheduled, doing inline for prototype)
            scorer.train()
            
            # 2. Predict
            score, factors = scorer.predict(instance)
            
            # 3. Save (Update only scoring fields to avoid loop)
            instance.risk_score = score
            instance.risk_factors = factors
            instance.save(update_fields=['risk_score', 'risk_factors'])
            print(f"--- ML: Claim Scored. Risk: {score}. Factors: {factors.keys()} ---")
            
        except Exception as e:
            print(f"--- ML Error: {e} ---")


@receiver(pre_save, sender=PaymentClaim)
def capture_old_status(sender, instance, **kwargs):
    """Capture the old status before saving"""
    if instance.pk:
        try:
            instance._old_status = PaymentClaim.objects.get(pk=instance.pk).status
        except PaymentClaim.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=PaymentClaim)
def route_and_notify_claim(sender, instance, created, **kwargs):
    """
    Handle auto-routing and notifications for payment claims.
    Tiered Approval:
    - < 10k: Project Manager
    - 10k - 100k: PM + Finance
    - > 100k: Director (Admin)
    - High Risk (>70): Escalates to Admin
    """
    if created:
        # Initial Routing
        route_claim_for_approval(instance)
        return
    
    # Check if status changed
    old_status = getattr(instance, '_old_status', None)
    if old_status and old_status != instance.status:
        
        # If status changed to SUBMITTED (e.g. from DRAFT or RE-SUBMITTED)
        if instance.status == PaymentClaim.Status.SUBMITTED:
            route_claim_for_approval(instance)
            
        # APPROVED: Notify contractor and finance team
        elif instance.status == PaymentClaim.Status.APPROVED:
            if instance.prepared_by:
                Notification.create_notification(
                    recipient=instance.prepared_by,
                    title="Payment Claim Approved",
                    message=f"Your payment claim #{instance.id[:8]} for ZMW {instance.amount:,.2f} has been approved.",
                    notification_type=Notification.Type.APPROVAL_GRANTED,
                    related_model='PaymentClaim',
                    related_id=str(instance.id)
                )
            
            # Reset assignment as it's approved
            instance.assigned_approver = None
            instance.save(update_fields=['assigned_approver'])
        
        # REJECTED: Notify contractor
        elif instance.status == PaymentClaim.Status.REJECTED:
            if instance.prepared_by:
                rejection_reason = instance.rejection_reason or "No reason provided"
                Notification.create_notification(
                    recipient=instance.prepared_by,
                    title="Payment Claim Rejected",
                    message=f"Your payment claim #{instance.id[:8]} was rejected. Reason: {rejection_reason}",
                    notification_type=Notification.Type.APPROVAL_DENIED,
                    related_model='PaymentClaim',
                    related_id=str(instance.id)
                )
            instance.assigned_approver = None
            instance.save(update_fields=['assigned_approver'])

        # PAID: Notify contractor
        elif instance.status == PaymentClaim.Status.PAID:
            if instance.prepared_by:
                Notification.create_notification(
                    recipient=instance.prepared_by,
                    title="Payment Processed",
                    message=f"Payment for claim #{instance.id[:8]} (ZMW {instance.amount:,.2f}) has been processed.",
                    notification_type=Notification.Type.PAYMENT_PROCESSED,
                    related_model='PaymentClaim',
                    related_id=str(instance.id)
                )


def route_claim_for_approval(instance):
    """
    Logic to determine the assigned approver based on rules.
    """
    amount = instance.amount
    risk_score = instance.risk_score or 0
    project = instance.contract.project
    
    # 1. High Risk Rule (Score > 70) -> Route to Admin
    if risk_score > 70:
        approver = User.objects.filter(role__is_admin=True).first()
        reason = "High Risk Level"
    # 2. Tier 3 Rule (> 100k) -> Route to Admin
    elif amount > 100000:
        approver = User.objects.filter(role__is_admin=True).first()
        reason = "Large Amount (> ZMW 100,000)"
    # 3. Tier 2 Rule (10k - 100k) -> Route to Finance/Manager
    elif amount > 10000:
        # Try to find a Finance user first
        approver = User.objects.filter(role__permissions__code='manage_finance').first()
        reason = "Medium Amount (ZMW 10,000 - 100,000)"
    # 4. Tier 1 Rule (< 10k) -> Route to Project Manager
    else:
        # Find manager from assigned team
        approver = project.assigned_team.filter(role__name__iexact='Manager').first()
        # Fallback to any manager if none assigned to project
        if not approver:
            approver = User.objects.filter(role__name__iexact='Manager').first()
        reason = "Small Amount (< ZMW 10,000)"

    if approver:
        # Check if already assigned to this approver to prevent loop
        if instance.assigned_approver == approver:
            return

        # Update assignment (avoid signal loop by using update_fields)
        instance.assigned_approver = approver
        instance.save(update_fields=['assigned_approver'])
        
        # Notify the assigned approver
        Notification.create_notification(
            recipient=approver,
            title="New Claim Assigned to You",
            message=f"Payment claim #{instance.id[:8]} for ZMW {instance.amount:,.2f} has been routed to you based on: {reason}.",
            notification_type=Notification.Type.TASK_ASSIGNED,
            related_model='PaymentClaim',
            related_id=str(instance.id)
        )
