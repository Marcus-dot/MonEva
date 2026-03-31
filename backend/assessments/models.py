from django.db import models
from projects.models import Milestone
from core.models import User
import uuid
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class Inspection(models.Model):
    class QualityVerdict(models.TextChoices):
        PASS = 'PASS', 'Pass'
        FAIL = 'FAIL', 'Fail'
        CONDITIONAL = 'CONDITIONAL', 'Conditional Pass'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='inspections')
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inspections')
    inspected_at = models.DateTimeField()
    
    # Inspection Data
    form_data = models.JSONField(default=dict)
    icare_compliance = models.JSONField(default=dict, help_text="I-CARE Values Checklist")
    location = models.JSONField(help_text="Expected GeoJSON point", null=True, blank=True)
    
    quality_verdict = models.CharField(max_length=20, choices=QualityVerdict.choices)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.milestone.title} - {self.quality_verdict}"

    def clean(self):
        """Validate inspection data"""
        errors = {}
        
        # Validate GPS coordinates if provided
        if self.location and isinstance(self.location, dict):
            coords = self.location.get('coordinates', [])
            if len(coords) >= 2:
                lng, lat = coords[0], coords[1]
                if not (-90 <= lat <= 90):
                    errors['location'] = 'Latitude must be between -90 and 90'
                if not (-180 <= lng <= 180):
                    errors['location'] = 'Longitude must be between -180 and 180'
        
        if errors:
            raise ValidationError(errors)

class Evidence(models.Model):
    class FileType(models.TextChoices):
        PHOTO = 'PHOTO', 'Photo'
        DOCUMENT = 'DOCUMENT', 'Document'
        VIDEO = 'VIDEO', 'Video'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection = models.ForeignKey(Inspection, on_delete=models.SET_NULL, null=True, blank=True, related_name='evidence')
    file = models.FileField(upload_to='evidence/%Y/%m/%d/')
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    metadata = models.JSONField(default=dict, help_text="EXIF, Timestamp, etc")
    image_hash = models.CharField(max_length=64, blank=True, null=True, help_text="Perceptual Hash for duplicate detection")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def calculate_hash(self):
        """Calculates VGG-style perceptual hash using imagehash library."""
        import imagehash
        from PIL import Image
        try:
            # Ensure file pointer is at start
            self.file.open()
            image = Image.open(self.file)
            # Use phash (Robust to rotation/scaling)
            return str(imagehash.phash(image))
        except Exception as e:
            print(f"Error hashing image: {e}")
            return None

    def save(self, *args, **kwargs):
        # 1. Calculate Hash if Photo
        if self.file_type == 'PHOTO' and not self.image_hash:
            self.image_hash = self.calculate_hash()
            
        # 2. Check for Duplicates (Excluding self)
        if self.image_hash:
            existing = Evidence.objects.filter(image_hash=self.image_hash).exclude(id=self.id)
            if existing.exists():
                from django.core.exceptions import ValidationError
                raise ValidationError(f"Duplicate image detected! This photo was already uploaded for Inspection {existing.first().inspection.milestone.title}.")
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Evidence for {self.inspection.id}"


# Signals
from django.db.models.signals import post_save
from django.dispatch import receiver
from projects.automation import sync_inspection_to_milestone

@receiver(post_save, sender=Inspection)
def inspection_sync_handler(sender, instance, **kwargs):
    sync_inspection_to_milestone(instance)


    

class EvaluationTemplate(models.Model):
    """
    Configurable questionnaire template for post-project evaluations.
    A default template auto-applies when a project is marked COMPLETED.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    questions = models.JSONField(
        default=list,
        help_text='List of question objects: [{id, label, type, required}]'
    )
    is_default = models.BooleanField(
        default=False,
        help_text='Auto-apply to all projects on completion if no template specified'
    )
    created_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, related_name='eval_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def save(self, *args, **kwargs):
        # Enforce at most one default template
        if self.is_default:
            EvaluationTemplate.objects.exclude(pk=self.pk).filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PostProjectEvaluation(models.Model):
    """
    One-time evaluation conducted after a project is marked COMPLETED.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        'projects.Project', on_delete=models.CASCADE, related_name='post_project_evaluation'
    )
    template = models.ForeignKey(
        EvaluationTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='evaluations'
    )
    sustainability_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='1 (Poor) to 5 (Excellent) likelihood of sustained impact'
    )
    objectives_achieved = models.BooleanField(
        default=False,
        help_text='Were the original project objectives fully achieved?'
    )
    responses = models.JSONField(
        default=dict,
        help_text='Answers keyed by question ID from template'
    )
    lessons_learned = models.TextField()
    future_recommendations = models.TextField()
    evaluated_at = models.DateTimeField(auto_now_add=True)
    evaluated_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Evaluation — {self.project.name}"


class ImpactFollowUp(models.Model):
    """
    Scheduled assessments (6, 12, 24 months post-completion).
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        MISSED = 'MISSED', 'Missed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='impact_followups')
    
    title = models.CharField(max_length=100, default="6-Month Follow-up")
    scheduled_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    outcomes_verified = models.TextField(blank=True, help_text="Summary of sustained outcomes observed")
    notes = models.TextField(blank=True)
    
    conducted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['scheduled_date']

    def __str__(self):
        return f"{self.title} - {self.project.name}"
