from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Inspection
from projects.models import Milestone


@receiver(post_save, sender=Inspection)
def update_milestone_status(sender, instance, created, **kwargs):
    """Automate Milestone status updates based on Inspection activity."""
    if created:
        milestone = instance.milestone
        if milestone.status == Milestone.Status.PENDING:
            milestone.status = Milestone.Status.IN_PROGRESS
            milestone.save()


# ── Auto-schedule ImpactFollowUp records when project is marked COMPLETED ────

@receiver(pre_save, sender='projects.Project')
def capture_old_project_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = sender.objects.get(pk=instance.pk).status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender='projects.Project')
def auto_schedule_impact_followups(sender, instance, created, **kwargs):
    """
    When a project moves to COMPLETED, auto-create ImpactFollowUp records
    at 6, 12, and 24 months post-completion so nothing falls through the cracks.
    """
    if created:
        return

    old_status = getattr(instance, '_old_status', None)
    if old_status == instance.status:
        return
    if instance.status != 'COMPLETED':
        return

    from .models import ImpactFollowUp
    from datetime import date, timedelta

    # Don't duplicate if already scheduled
    if ImpactFollowUp.objects.filter(project=instance).exists():
        return

    base_date = instance.end_date or date.today()
    followups = [
        ('6-Month Follow-up Evaluation', 180),
        ('12-Month Follow-up Evaluation', 365),
        ('24-Month Follow-up Evaluation', 730),
    ]
    for title, days in followups:
        ImpactFollowUp.objects.create(
            project=instance,
            title=title,
            scheduled_date=base_date + timedelta(days=days),
            status=ImpactFollowUp.Status.PENDING,
        )
