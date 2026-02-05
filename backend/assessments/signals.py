from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Inspection
from projects.models import Milestone

@receiver(post_save, sender=Inspection)
def update_milestone_status(sender, instance, created, **kwargs):
    """
    Automate Milestone status updates based on Inspection activity.
    """
    if created:
        milestone = instance.milestone
        # If this is the first inspection, mark the milestone as IN_PROGRESS
        if milestone.status == Milestone.Status.PENDING:
            milestone.status = Milestone.Status.IN_PROGRESS
            milestone.save()
            
        # TODO: If verdict is FAIL, we could trigger alerts here.
