from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Project
from indicators.models import Indicator, IndicatorTarget

@receiver(m2m_changed, sender=Project.themes.through)
def auto_assign_indicators_on_theme_change(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    When themes are added to a Project, auto-assign STANDARD indicators linked to those themes.
    """
    if action == "post_add" and not reverse:
        # distinct themes added
        themes_added = model.objects.filter(pk__in=pk_set)
        
        for theme in themes_added:
            # Find all STANDARD indicators for this theme
            standard_indicators = Indicator.objects.filter(
                theme=theme, 
                category=Indicator.Category.STANDARD
            )
            
            for ind in standard_indicators:
                # Create Target if not exists
                IndicatorTarget.objects.get_or_create(
                    project=instance,
                    indicator=ind,
                    defaults={
                        'target_value': 0, # Default, user needs to set this
                        'description': f"Auto-generated from theme: {theme.name}"
                    }
                )
