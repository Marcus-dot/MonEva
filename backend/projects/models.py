from django.db import models
from core.models import Organization
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class SDG(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True, help_text="e.g. SDG1")
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#000000") # Hex code

    def __str__(self):
        return f"{self.code}: {self.name}"

    class Meta:
        verbose_name = "Sustainable Development Goal"
        verbose_name_plural = "Sustainable Development Goals"

class StrategicTheme(models.Model):
    """
    Dynamic Strategic Themes for multi-tagging projects.
    Replaces the hardcoded StrategicTheme choices eventually.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True, help_text="Short code e.g. 'WASH'")
    color = models.CharField(max_length=7, default="#CCCCCC", help_text="Hex color for UI tags")
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Project(models.Model):
    class Types(models.TextChoices):
        ROAD = 'ROAD', 'Road'
        BUILDING = 'BUILDING', 'Building'
        CSR = 'CSR', 'CSR'

    class Status(models.TextChoices):
        PLANNING = 'PLANNING', 'Planning'
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        ON_HOLD = 'ON_HOLD', 'On Hold'

    class CsrFocus(models.TextChoices):
        HEALTH = 'HEALTH', 'Health'
        EDUCATION = 'EDUCATION', 'Education'
        ENVIRONMENT = 'ENVIRONMENT', 'Environment'
        INFRASTRUCTURE = 'INFRASTRUCTURE', 'Infrastructure'
        OTHER = 'OTHER', 'Other'

    class StrategicTheme(models.TextChoices):
        EDUCATION = 'EDUCATION', 'Education & Skills'
        HEALTH = 'HEALTH', 'Health'
        WASH = 'WASH', 'Water, Sanitation & Hygiene'
        AGRICULTURE = 'AGRICULTURE', 'Agriculture'
        ENVIRONMENT = 'ENVIRONMENT', 'Environment & Climate'
        ENERGY = 'ENERGY', 'Energy & Infrastructure'
        GENDER_EQUALITY = 'GENDER_EQUALITY', 'Gender Equality & Empowerment'
        CLIMATE_ADAPTATION = 'CLIMATE_ADAPTATION', 'Climate Change Adaptation'
        OTHER = 'OTHER', 'Other'

    class KeyResultArea(models.TextChoices):
        SOCIO_ECONOMIC = 'SOCIO_ECONOMIC', 'Socio-Economic Development'
        REPUTATION = 'REPUTATION', 'Corporate Brand Reputation'
        FINANCIAL = 'FINANCIAL', 'Financial Sustainability'
        OPERATIONAL = 'OPERATIONAL', 'Operational Excellence'
        

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=Types.choices)
    csr_focus = models.CharField(max_length=20, choices=CsrFocus.choices, null=True, blank=True)
    
    # Strategic Mapping
    # New Multi-Thematic Support
    themes = models.ManyToManyField('StrategicTheme', related_name='projects', blank=True)
    
    # Legacy Field (Deprecating)
    thematic_area = models.CharField(
        max_length=20, 
        choices=StrategicTheme.choices, 
        default=StrategicTheme.OTHER
    )
    primary_kra = models.CharField(
        max_length=20,
        choices=KeyResultArea.choices,
        default=KeyResultArea.SOCIO_ECONOMIC
    )
    sdgs = models.ManyToManyField(SDG, related_name='projects', blank=True)

    description = models.TextField(blank=True)
    location = models.JSONField(help_text="Expected GeoJSON point (Center)", null=True, blank=True)
    catchment_area = models.JSONField(
        null=True, 
        blank=True, 
        help_text="GeoJSON Polygon defining the project's service area"
    ) 
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitude coordinate")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNING)
    owner_org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')

    
    # Phase 4: Collaboration
    assigned_team = models.ManyToManyField('core.User', related_name='assigned_projects', blank=True)
    partners = models.ManyToManyField(Organization, related_name='partner_projects', blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

    def clean(self):
        """Validate project data"""
        from django.core.exceptions import ValidationError
        errors = {}
        
        # Validate date range
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                errors['end_date'] = 'End date must be after start date'
        
        # Validate coordinates if provided
        if self.latitude is not None:
            if not (-90 <= self.latitude <= 90):
                errors['latitude'] = 'Latitude must be between -90 and 90'
        
        if self.longitude is not None:
            if not (-180 <= self.longitude <= 180):
                errors['longitude'] = 'Longitude must be between -180 and 180'
        
        if errors:
            raise ValidationError(errors)

class Contract(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACTIVE = 'ACTIVE', 'Active'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        CLOSED = 'CLOSED', 'Closed'
        EXPIRED = 'EXPIRED', 'Expired'

    class ContractType(models.TextChoices):
        WORKS = 'WORKS', 'Works'
        SUPPLY = 'SUPPLY', 'Supply of Goods'
        SERVICE = 'SERVICE', 'Service'
        CONSULTANCY = 'CONSULTANCY', 'Consultancy'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='contracts')
    contractor = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='contracts')

    # Core identification
    contract_number = models.CharField(max_length=100, blank=True, help_text="e.g. KGLCDC/2026/001")
    contract_type = models.CharField(max_length=20, choices=ContractType.choices, default=ContractType.WORKS)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # Financial
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZMW')
    retention_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00,
        help_text="Retention % withheld until defects liability period ends"
    )

    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    defects_liability_period = models.PositiveIntegerField(
        default=365,
        help_text="Defects liability period in days after completion"
    )

    # Location & scope
    chiefdom = models.CharField(max_length=100, blank=True, help_text="Chiefdom/ward where works are executed")
    scope_of_works = models.TextField(blank=True)
    payment_terms = models.TextField(blank=True, help_text="e.g. 30 days from certified invoice")

    # Document
    document = models.FileField(upload_to='contracts/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.contract_number or self.id} — {self.contractor.name}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.end_date < timezone.now().date() and self.status == self.Status.ACTIVE


class ContractAmendment(models.Model):
    """Tracks changes made to a contract after signing (variations/extensions)"""
    class AmendmentType(models.TextChoices):
        EXTENSION = 'EXTENSION', 'Time Extension'
        VARIATION = 'VARIATION', 'Variation Order'
        SCOPE_CHANGE = 'SCOPE_CHANGE', 'Scope Change'
        VALUE_ADJUSTMENT = 'VALUE_ADJUSTMENT', 'Value Adjustment'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='amendments')
    amendment_type = models.CharField(max_length=20, choices=AmendmentType.choices)
    amendment_number = models.PositiveIntegerField(help_text="Sequential amendment number")
    description = models.TextField()

    # For time extensions
    original_end_date = models.DateField(null=True, blank=True)
    new_end_date = models.DateField(null=True, blank=True)

    # For value adjustments
    original_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    new_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    approved_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    document = models.FileField(upload_to='contract_amendments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['contract', 'amendment_number']
        unique_together = [('contract', 'amendment_number')]

    def __str__(self):
        return f"Amendment #{self.amendment_number} — {self.contract}"

class Milestone(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        help_text="Physical completion % required",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    value_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    def __str__(self):
        return self.title

    def clean(self):
        """Validate milestone data"""
        errors = {}
        
        # Validate due_date is within contract period
        if self.contract and self.due_date:
            if self.due_date < self.contract.start_date:
                errors['due_date'] = 'Due date cannot be before contract start date'
            if self.due_date > self.contract.end_date:
                errors['due_date'] = 'Due date cannot be after contract end date'
        
        # Validate value_amount doesn't exceed contract total
        if self.contract and self.value_amount:
            if self.value_amount > self.contract.total_value:
                errors['value_amount'] = 'Milestone value cannot exceed contract total value'
        
        if errors:
            raise ValidationError(errors)


class ProjectComment(models.Model):
    """Comments/notes on projects for team collaboration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, related_name='project_comments')
    comment = models.TextField()
    assigned_to = models.ForeignKey(
        'core.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_project_tasks',
        help_text="Turn this comment into a task by assigning it to someone"
    )
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-created_at']

class BeneficiaryFeedback(models.Model):
    class Sentiment(models.TextChoices):
        POSITIVE = 'POSITIVE', 'Positive'
        NEUTRAL = 'NEUTRAL', 'Neutral'
        NEGATIVE = 'NEGATIVE', 'Negative'

    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'
        PREFER_NOT_TO_SAY = 'PNTS', 'Prefer not to say'

    class AgeGroup(models.TextChoices):
        CHILD = '0-14', '0-14'
        YOUTH = '15-24', '15-24'
        ADULT = '25-64', '25-64'
        ELDERLY = '65+', '65+'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='feedback')
    milestone = models.ForeignKey(Milestone, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback')
    
    content = models.TextField()
    sentiment = models.CharField(max_length=10, choices=Sentiment.choices, default=Sentiment.NEUTRAL)
    
    # Demographics for Equity Tracking
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    age_group = models.CharField(max_length=10, choices=AgeGroup.choices, blank=True)
    location_coords = models.CharField(max_length=100, blank=True, help_text="Lat,Lng string")
    
    beneficiary_id = models.CharField(max_length=100, blank=True, help_text="Anonymous ID or name")
    beneficiary_profile = models.ForeignKey('Beneficiary', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_items')
    contact_info = models.CharField(max_length=100, blank=True, help_text="Phone or Email")
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='collected_feedback')

    def __str__(self):
        return f"Feedback for {self.project.name} on {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-created_at']

class Beneficiary(models.Model):
    """
    Profile of an individual beneficiary for long-term tracking.
    """
    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='beneficiaries')
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    year_of_birth = models.IntegerField(null=True, blank=True)
    
    contact_info = models.CharField(max_length=100, blank=True, help_text="Phone or Email")
    location = models.CharField(max_length=255, blank=True, help_text="Village/Community")
    
    # Impact Metrics
    disability_status = models.BooleanField(default=False)
    vulnerability_category = models.CharField(
        max_length=50, 
        blank=True, 
        choices=[
            ('ELDERLY', 'Elderly'),
            ('ORPHAN', 'Orphan'),
            ('DISABLED', 'Disabled'),
            ('LOW_INCOME', 'Low Income'),
            ('OTHER', 'Other')
        ]
    )
    residence_type = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('URBAN', 'Urban'),
            ('RURAL', 'Rural'),
            ('PERI_URBAN', 'Peri-urban')
        ]
    )
    
    # Metadata for filtering
    is_vulnerable = models.BooleanField(default=False, help_text="Disabled, Elderly, Child-headed household etc.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

